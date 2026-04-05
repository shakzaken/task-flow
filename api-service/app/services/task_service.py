from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import ValidationError

from app.db.models.task import Task
from app.db.repositories.task_repository import TaskRepository
from app.schemas.task import (
    CreateTaskRequest,
    CreateTaskResponse,
    ResizeImagePayload,
    TaskResponse,
    TaskStatus,
)
from app.services.publisher import Publisher
from app.services.storage import StorageService


class TaskValidationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class TaskNotFoundError(Exception):
    def __init__(self, task_id: UUID) -> None:
        self.message = f"Task {task_id} was not found."
        super().__init__(self.message)


class TaskService:
    def __init__(
        self,
        repository: TaskRepository,
        storage: StorageService,
        publisher: Publisher,
    ) -> None:
        self.repository = repository
        self.storage = storage
        self.publisher = publisher

    def create_task(self, request: CreateTaskRequest) -> CreateTaskResponse:
        # Phase 1 accepts the known reliability gap where the DB commit can
        # succeed and the publish can still fail afterward.
        try:
            validated_payload = request.validate_payload()
        except ValidationError as exc:
            raise TaskValidationError(str(exc)) from exc

        task_id = uuid4()
        payload = validated_payload.model_dump()

        if isinstance(validated_payload, ResizeImagePayload):
            payload["image_path"] = self.storage.attach_temporary_upload(
                temporary_path=validated_payload.image_path,
                task_id=str(task_id),
            )

        try:
            self.repository.create_task(
                task_id=task_id,
                task_type=request.task_type,
                status=TaskStatus.PENDING,
                payload=payload,
            )
            self.repository.save()
        except Exception:
            self.repository.rollback()
            raise

        self.publisher.publish_task_created(task_id=task_id, task_type=request.task_type)
        return CreateTaskResponse(task_id=task_id, status=TaskStatus.PENDING)

    def get_task(self, task_id: UUID) -> TaskResponse:
        task = self.repository.get_task_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return self._to_task_response(task)

    def cleanup_stale_uploads(self, ttl_seconds: int) -> list[str]:
        return self.storage.cleanup_stale_uploads(ttl_seconds)

    @staticmethod
    def _to_task_response(task: Task) -> TaskResponse:
        return TaskResponse(
            id=task.id,
            type=task.task_type,
            status=task.task_status,
            payload=task.payload,
            result=task.result,
            error_message=task.error_message,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
