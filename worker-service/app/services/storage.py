from __future__ import annotations

import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from uuid import UUID

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError


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
        work_root: Path | None = None,
        output_root: str = "outputs",
    ) -> None:
        self.bucket = bucket
        self.region = region
        self.endpoint_url = endpoint_url
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.use_ssl = use_ssl
        self.force_path_style = force_path_style
        self.auto_create_bucket = auto_create_bucket
        self.work_root = work_root or Path(tempfile.gettempdir()) / "task-flow-worker"
        self.output_root = output_root.strip("/") or "outputs"
        addressing_style = "path" if force_path_style else "virtual"
        self.client = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            use_ssl=use_ssl,
            config=BotoConfig(s3={"addressing_style": addressing_style}),
        )

    def ensure_ready(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as exc:
            if not self.auto_create_bucket or self._error_code(exc) not in {"404", "NoSuchBucket"}:
                raise
            create_args: dict[str, object] = {"Bucket": self.bucket}
            if self.region != "us-east-1":
                create_args["CreateBucketConfiguration"] = {"LocationConstraint": self.region}
            self.client.create_bucket(**create_args)

    def close(self) -> None:
        self.client.close()

    @contextmanager
    def task_workspace(self, task_id: UUID):
        workspace = Path(tempfile.mkdtemp(prefix=f"{task_id}-", dir=self.work_root))
        try:
            yield workspace
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    def download_to_path(self, relative_path: str, destination: Path) -> Path:
        object_key = self.normalize_key(relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.client.download_file(self.bucket, object_key, str(destination))
        except ClientError as exc:
            if self._error_code(exc) in {"404", "NoSuchKey"}:
                raise FileNotFoundError(f"Input artifact does not exist: {relative_path}") from exc
            raise
        return destination

    def upload_file(self, source_path: Path, relative_path: str, content_type: str | None = None) -> str:
        object_key = self.normalize_key(relative_path)
        extra_args = {"ContentType": content_type} if content_type else None
        if extra_args is None:
            self.client.upload_file(str(source_path), self.bucket, object_key)
        else:
            self.client.upload_file(str(source_path), self.bucket, object_key, ExtraArgs=extra_args)
        return object_key

    def build_output_relative_path(self, task_id: UUID, source_relative_path: str) -> str:
        suffix = PurePosixPath(source_relative_path).suffix or ".jpg"
        return (PurePosixPath(self.output_root) / str(task_id) / f"output{suffix}").as_posix()

    @staticmethod
    def normalize_key(relative_path: str) -> str:
        candidate = PurePosixPath(relative_path)
        if candidate.is_absolute() or any(part in {"..", "."} for part in candidate.parts):
            raise ValueError("Path must stay inside the storage bucket namespace.")
        normalized = candidate.as_posix().lstrip("/")
        if not normalized:
            raise ValueError("Path must not be empty.")
        return normalized

    @staticmethod
    def _error_code(exc: ClientError) -> str:
        return str(exc.response.get("Error", {}).get("Code", ""))

