from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi import UploadFile

from app.services.storage import StorageService


def test_storage_writes_under_shared_root(tmp_path: Path) -> None:
    storage = StorageService(tmp_path / "shared")
    upload = UploadFile(filename="file.txt", file=BytesIO(b"content"))

    response = storage.store_temporary_upload(upload)

    stored_path = storage.resolve_relative_path(response.path)
    assert stored_path.exists()
    assert stored_path.is_file()
    assert tmp_path / "shared" in stored_path.parents
