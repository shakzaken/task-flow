from __future__ import annotations

from pathlib import Path
from uuid import UUID


class StorageService:
    def __init__(self, root_path: Path, output_root: str = "outputs") -> None:
        self.root_path = root_path
        self.output_root = output_root.strip("/") or "outputs"

    def resolve_relative_path(self, relative_path: str) -> Path:
        candidate = (self.root_path / relative_path).resolve()
        root = self.root_path.resolve()
        if root not in candidate.parents and candidate != root:
            raise ValueError("Path must stay inside the shared storage root.")
        return candidate

    def ensure_parent_directory(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

    def build_output_relative_path(self, task_id: UUID, source_relative_path: str) -> str:
        suffix = Path(source_relative_path).suffix or ".jpg"
        return (Path(self.output_root) / str(task_id) / f"output{suffix}").as_posix()
