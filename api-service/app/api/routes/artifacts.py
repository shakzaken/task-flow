from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.api.dependencies import get_storage_service
from app.services.storage import StorageService

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("/{relative_path:path}")
async def get_artifact(
    relative_path: str,
    storage_service: StorageService = Depends(get_storage_service),
) -> FileResponse:
    artifact_path = storage_service.resolve_relative_path(relative_path)
    if not artifact_path.exists() or not artifact_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact was not found.")

    return FileResponse(path=artifact_path, filename=Path(relative_path).name)
