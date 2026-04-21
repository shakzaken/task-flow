from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import PurePosixPath

from fastapi import HTTPException, UploadFile, status

from app.schemas.upload import UploadResponse
from app.services.storage import ArtifactStream, StorageService


@dataclass
class StoredObject:
    body: bytes
    last_modified: datetime
    content_type: str | None = None


class FakeStorageService(StorageService):
    def __init__(self) -> None:
        self.objects: dict[str, StoredObject] = {}
        self.bucket = "test-bucket"

    async def ensure_ready(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def store_temporary_upload(self, upload_file: UploadFile) -> UploadResponse:
        filename = upload_file.filename or "upload.bin"
        suffix = PurePosixPath(filename).suffix
        upload_id = f"upload-{len(self.objects) + 1}"
        key = f"uploads/tmp/{upload_id}{suffix}"
        body = await upload_file.read()
        await upload_file.close()
        self.objects[key] = StoredObject(
            body=body,
            last_modified=datetime.now(timezone.utc),
            content_type=upload_file.content_type,
        )
        return UploadResponse(upload_id=upload_id, path=key, filename=filename)

    async def attach_temporary_upload(self, temporary_path: str, task_id: str, destination_stem: str = "input") -> str:
        source_key = self.normalize_key(temporary_path)
        source = self.objects.get(source_key)
        if source is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Temporary upload reference does not exist.",
            )
        suffix = PurePosixPath(source_key).suffix
        destination_key = f"uploads/tasks/{task_id}/{destination_stem}{suffix}"
        self.objects[destination_key] = StoredObject(
            body=source.body,
            last_modified=datetime.now(timezone.utc),
            content_type=source.content_type,
        )
        del self.objects[source_key]
        return destination_key

    async def cleanup_stale_uploads(self, ttl_seconds: int) -> list[str]:
        cutoff = datetime.now(timezone.utc).timestamp() - ttl_seconds
        deleted: list[str] = []
        for key, stored in list(self.objects.items()):
            if key.startswith("uploads/tmp/") and stored.last_modified.timestamp() < cutoff:
                deleted.append(key)
                del self.objects[key]
        return deleted

    async def get_artifact(self, relative_path: str) -> ArtifactStream:
        object_key = self.normalize_key(relative_path)
        stored = self.objects.get(object_key)
        if stored is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact was not found.")

        async def stream():
            yield stored.body

        return ArtifactStream(
            body=stream(),
            filename=PurePosixPath(object_key).name,
            media_type=stored.content_type,
        )

    @staticmethod
    def normalize_key(relative_path: str) -> str:
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
