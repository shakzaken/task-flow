from __future__ import annotations

from io import BytesIO

import pytest
from fastapi import UploadFile

from app.services.storage import StorageService


@pytest.mark.anyio
async def test_storage_returns_temporary_object_key(storage_service: StorageService) -> None:
    upload = UploadFile(filename="file.txt", file=BytesIO(b"content"))

    response = await storage_service.store_temporary_upload(upload)

    assert response.path.startswith("uploads/tmp/")
