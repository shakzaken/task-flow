from __future__ import annotations

import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.schemas.upload import UploadResponse


class StorageService:
    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path
        self.root_path.mkdir(parents=True, exist_ok=True)

    def store_temporary_upload(self, upload_file: UploadFile) -> UploadResponse:
        filename = upload_file.filename or "upload.bin"
        suffix = Path(filename).suffix
        upload_id = uuid4().hex
        relative_path = Path("uploads") / "tmp" / f"{upload_id}{suffix}"
        destination = self.resolve_relative_path(relative_path.as_posix())
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as file_handle:
            shutil.copyfileobj(upload_file.file, file_handle)
        return UploadResponse(upload_id=upload_id, path=relative_path.as_posix(), filename=filename)

    def attach_temporary_upload(self, temporary_path: str, task_id: str) -> str:
        source = self.resolve_relative_path(temporary_path)
        if not source.exists() or not source.is_file():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Temporary upload reference does not exist.",
            )

        suffix = source.suffix
        relative_destination = Path("uploads") / "tasks" / task_id / f"input{suffix}"
        destination = self.resolve_relative_path(relative_destination.as_posix())
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source.as_posix(), destination.as_posix())
        return relative_destination.as_posix()

    def resolve_relative_path(self, relative_path: str) -> Path:
        candidate = (self.root_path / relative_path).resolve()
        root = self.root_path.resolve()
        if root not in candidate.parents and candidate != root:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Upload path must stay inside the shared storage root.",
            )
        return candidate

    def cleanup_stale_uploads(self, ttl_seconds: int) -> list[str]:
        # Phase 1 runs cleanup through a service method that can be invoked by a
        # scheduled job or management command outside request handlers.
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=ttl_seconds)
        uploads_root = self.root_path / "uploads" / "tmp"
        deleted: list[str] = []
        if not uploads_root.exists():
            return deleted

        for path in uploads_root.iterdir():
            if not path.is_file():
                continue
            modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if modified_at < cutoff:
                deleted.append(path.relative_to(self.root_path).as_posix())
                path.unlink()

        return deleted
