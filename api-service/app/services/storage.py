from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import aiofiles
import aiofiles.os
import aiofiles.ospath
from anyio import Path as AsyncPath
from fastapi import HTTPException, UploadFile, status

from app.schemas.upload import UploadResponse


class StorageService:
    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path

    async def store_temporary_upload(self, upload_file: UploadFile) -> UploadResponse:
        filename = upload_file.filename or "upload.bin"
        suffix = Path(filename).suffix
        upload_id = uuid4().hex
        relative_path = Path("uploads") / "tmp" / f"{upload_id}{suffix}"
        destination = self.resolve_relative_path(relative_path.as_posix())
        await AsyncPath(destination.parent).mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(destination, "wb") as file_handle:
            while chunk := await upload_file.read(1024 * 1024):
                await file_handle.write(chunk)
        await upload_file.close()
        return UploadResponse(upload_id=upload_id, path=relative_path.as_posix(), filename=filename)

    async def attach_temporary_upload(self, temporary_path: str, task_id: str) -> str:
        source = self.resolve_relative_path(temporary_path)
        if not await aiofiles.ospath.exists(source) or not await aiofiles.ospath.isfile(source):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Temporary upload reference does not exist.",
            )

        suffix = source.suffix
        relative_destination = Path("uploads") / "tasks" / task_id / f"input{suffix}"
        destination = self.resolve_relative_path(relative_destination.as_posix())
        await AsyncPath(destination.parent).mkdir(parents=True, exist_ok=True)
        await aiofiles.os.rename(source, destination)
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

    async def cleanup_stale_uploads(self, ttl_seconds: int) -> list[str]:
        # Phase 1 runs cleanup through a service method that can be invoked by a
        # scheduled job or management command outside request handlers.
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=ttl_seconds)
        uploads_root = self.root_path / "uploads" / "tmp"
        deleted: list[str] = []
        if not await aiofiles.ospath.exists(uploads_root):
            return deleted

        async for path in AsyncPath(uploads_root).iterdir():
            resolved_path = Path(str(path))
            if not await aiofiles.ospath.isfile(resolved_path):
                continue
            stat_result = await aiofiles.os.stat(resolved_path)
            modified_at = datetime.fromtimestamp(stat_result.st_mtime, tz=timezone.utc)
            if modified_at < cutoff:
                deleted.append(resolved_path.relative_to(self.root_path).as_posix())
                await aiofiles.os.remove(resolved_path)

        return deleted
