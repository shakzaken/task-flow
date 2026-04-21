from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_storage_service
from app.services.storage import StorageService

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("/{relative_path:path}")
async def get_artifact(
    relative_path: str,
    storage_service: StorageService = Depends(get_storage_service),
) -> StreamingResponse:
    artifact = await storage_service.get_artifact(relative_path)
    return StreamingResponse(
        artifact.body,
        media_type=artifact.media_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{artifact.filename}"'},
    )
