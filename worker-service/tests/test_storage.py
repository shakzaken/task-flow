from uuid import uuid4

import pytest

from app.services.storage import StorageService


def test_normalize_key_accepts_bucket_relative_paths() -> None:
    resolved = StorageService.normalize_key("uploads/tasks/abc/input.jpg")

    assert resolved == "uploads/tasks/abc/input.jpg"


def test_normalize_key_rejects_escape() -> None:
    with pytest.raises(ValueError):
        StorageService.normalize_key("../outside.txt")


def test_build_output_relative_path_uses_task_scope(storage_service: StorageService) -> None:
    storage = storage_service

    output_path = storage.build_output_relative_path(uuid4(), "uploads/tasks/id/input.png")

    assert output_path.startswith("outputs/")
    assert output_path.endswith("/output.png")
