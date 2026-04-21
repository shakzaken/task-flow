from __future__ import annotations

import inspect
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import PurePosixPath
from uuid import uuid4

import aioboto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile, status

from app.schemas.upload import UploadResponse


@dataclass(frozen=True)
class ArtifactStream:
    body: AsyncIterator[bytes]
    filename: str
    media_type: str | None


class StorageService:
    def __init__(
        self,
        bucket: str,
        region: str,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        use_ssl: bool = True,
        force_path_style: bool = False,
        auto_create_bucket: bool = False,
    ) -> None:
        self.bucket = bucket
        self.region = region
        self.endpoint_url = endpoint_url
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.use_ssl = use_ssl
        self.force_path_style = force_path_style
        self.auto_create_bucket = auto_create_bucket
        self.session = aioboto3.Session()
        addressing_style = "path" if force_path_style else "virtual"
        self.client_config = BotoConfig(s3={"addressing_style": addressing_style})

    async def ensure_ready(self) -> None:
        async with self._client() as client:
            try:
                await client.head_bucket(Bucket=self.bucket)
            except ClientError as exc:
                if not self.auto_create_bucket or self._error_code(exc) not in {"404", "NoSuchBucket"}:
                    raise
                create_args: dict[str, object] = {"Bucket": self.bucket}
                if self.region != "us-east-1":
                    create_args["CreateBucketConfiguration"] = {"LocationConstraint": self.region}
                await client.create_bucket(**create_args)

    async def close(self) -> None:
        return None

    async def store_temporary_upload(self, upload_file: UploadFile) -> UploadResponse:
        filename = upload_file.filename or "upload.bin"
        suffix = PurePosixPath(filename).suffix
        upload_id = uuid4().hex
        relative_path = PurePosixPath("uploads") / "tmp" / f"{upload_id}{suffix}"
        object_key = self._normalize_key(relative_path.as_posix())
        body = bytearray()
        while chunk := await upload_file.read(1024 * 1024):
            body.extend(chunk)
        await upload_file.close()

        async with self._client() as client:
            await client.put_object(Bucket=self.bucket, Key=object_key, Body=bytes(body))

        return UploadResponse(upload_id=upload_id, path=object_key, filename=filename)

    async def attach_temporary_upload(
        self,
        temporary_path: str,
        task_id: str,
        destination_stem: str = "input",
    ) -> str:
        source_key = self._normalize_key(temporary_path)
        suffix = PurePosixPath(source_key).suffix
        relative_destination = PurePosixPath("uploads") / "tasks" / task_id / f"{destination_stem}{suffix}"
        destination_key = self._normalize_key(relative_destination.as_posix())

        async with self._client() as client:
            try:
                await client.head_object(Bucket=self.bucket, Key=source_key)
            except ClientError as exc:
                if self._error_code(exc) in {"404", "NoSuchKey"}:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail="Temporary upload reference does not exist.",
                    ) from exc
                raise

            await client.copy_object(
                Bucket=self.bucket,
                CopySource={"Bucket": self.bucket, "Key": source_key},
                Key=destination_key,
            )
            await client.delete_object(Bucket=self.bucket, Key=source_key)

        return destination_key

    async def cleanup_stale_uploads(self, ttl_seconds: int) -> list[str]:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=ttl_seconds)
        deleted: list[str] = []
        continuation_token: str | None = None

        async with self._client() as client:
            while True:
                list_kwargs: dict[str, object] = {
                    "Bucket": self.bucket,
                    "Prefix": "uploads/tmp/",
                    "MaxKeys": 1000,
                }
                if continuation_token is not None:
                    list_kwargs["ContinuationToken"] = continuation_token
                response = await client.list_objects_v2(**list_kwargs)

                for item in response.get("Contents", []):
                    key = str(item["Key"])
                    modified_at = item["LastModified"]
                    if modified_at < cutoff:
                        await client.delete_object(Bucket=self.bucket, Key=key)
                        deleted.append(key)

                if not response.get("IsTruncated"):
                    break
                continuation_token = response.get("NextContinuationToken")

        return deleted

    async def get_artifact(self, relative_path: str) -> ArtifactStream:
        object_key = self._normalize_key(relative_path)
        client_manager = self._client()
        client = await client_manager.__aenter__()

        try:
            response = await client.get_object(Bucket=self.bucket, Key=object_key)
        except ClientError as exc:
            await client_manager.__aexit__(type(exc), exc, exc.__traceback__)
            if self._error_code(exc) in {"404", "NoSuchKey"}:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact was not found.") from exc
            raise

        body = response["Body"]
        media_type = response.get("ContentType")

        async def stream() -> AsyncIterator[bytes]:
            try:
                while chunk := await body.read(1024 * 1024):
                    yield chunk
            finally:
                close_result = body.close()
                if inspect.isawaitable(close_result):
                    await close_result
                await client_manager.__aexit__(None, None, None)

        return ArtifactStream(
            body=stream(),
            filename=PurePosixPath(object_key).name,
            media_type=media_type,
        )

    def _client(self):
        return self.session.client(
            "s3",
            region_name=self.region,
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            use_ssl=self.use_ssl,
            config=self.client_config,
        )

    @staticmethod
    def _normalize_key(relative_path: str) -> str:
        candidate = PurePosixPath(relative_path)
        if candidate.is_absolute() or any(part in {"..", "."} for part in candidate.parts):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Upload path must stay inside the storage bucket namespace.",
            )

        normalized = candidate.as_posix().lstrip("/")
        if not normalized:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Upload path must not be empty.",
            )
        return normalized

    @staticmethod
    def _error_code(exc: ClientError) -> str:
        return str(exc.response.get("Error", {}).get("Code", ""))
