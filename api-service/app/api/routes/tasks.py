from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_task_service
from app.schemas.task import CreateTaskRequest, CreateTaskResponse, TaskResponse
from app.services.task_service import (
    TaskNotFoundError,
    TaskService,
    TaskValidationError,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=CreateTaskResponse, status_code=status.HTTP_202_ACCEPTED)
def create_task(
    request: CreateTaskRequest,
    task_service: TaskService = Depends(get_task_service),
) -> CreateTaskResponse:
    try:
        return task_service.create_task(request)
    except TaskValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=exc.message,
        ) from exc


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: UUID,
    task_service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    try:
        return task_service.get_task(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
