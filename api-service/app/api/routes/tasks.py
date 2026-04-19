from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import PositiveInt

from app.api.dependencies import get_task_service
from app.schemas.task import CreateTaskRequest, CreateTaskResponse, TaskListResponse, TaskResponse
from app.services.task_service import (
    TaskNotFoundError,
    TaskService,
    TaskValidationError,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=CreateTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_task(
    request: CreateTaskRequest,
    task_service: TaskService = Depends(get_task_service),
) -> CreateTaskResponse:
    try:
        return await task_service.create_task(request)
    except TaskValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=exc.message,
        ) from exc


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    limit: PositiveInt = 10,
    task_service: TaskService = Depends(get_task_service),
) -> TaskListResponse:
    return await task_service.list_recent_tasks(min(limit, 50))


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    task_service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    try:
        return await task_service.get_task(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
