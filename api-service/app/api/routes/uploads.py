from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.dependencies import get_storage_service
from app.schemas.upload import UploadResponse
from app.services.storage import StorageService

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
def upload_file(
    file: UploadFile = File(...),
    storage_service: StorageService = Depends(get_storage_service),
) -> UploadResponse:
    return storage_service.store_temporary_upload(file)

