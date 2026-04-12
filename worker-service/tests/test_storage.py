from pathlib import Path
from uuid import uuid4

import pytest

from app.services.storage import StorageService


def test_resolve_relative_path_stays_under_root(tmp_path: Path) -> None:
    storage = StorageService(tmp_path)

    resolved = storage.resolve_relative_path("uploads/tasks/abc/input.jpg")

    assert resolved == (tmp_path / "uploads" / "tasks" / "abc" / "input.jpg").resolve()


def test_resolve_relative_path_rejects_escape(tmp_path: Path) -> None:
    storage = StorageService(tmp_path)

    with pytest.raises(ValueError):
        storage.resolve_relative_path("../outside.txt")


def test_build_output_relative_path_uses_task_scope(tmp_path: Path) -> None:
    storage = StorageService(tmp_path, "outputs")

    output_path = storage.build_output_relative_path(uuid4(), "uploads/tasks/id/input.png")

    assert output_path.startswith("outputs/")
    assert output_path.endswith("/output.png")
