from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.task import Task
from app.schemas import TaskStatus, TaskType


class TaskRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_task(
        self,
        task_id: UUID,
        task_type: TaskType,
        status: TaskStatus,
        payload: dict,
    ) -> Task:
        task = Task(
            id=task_id,
            type=task_type.value,
            status=status.value,
            payload=payload,
            result=None,
            error_message=None,
        )
        self.session.add(task)
        self.session.flush()
        self.session.refresh(task)
        return task

    def get_task_by_id(self, task_id: UUID) -> Task | None:
        return self.session.get(Task, task_id)

    def mark_processing(self, task: Task) -> Task:
        task.status = TaskStatus.PROCESSING.value
        task.error_message = None
        task.updated_at = datetime.now(timezone.utc)
        self.session.add(task)
        self.session.flush()
        self.session.refresh(task)
        return task

    def mark_completed(self, task: Task, result: dict) -> Task:
        task.status = TaskStatus.COMPLETED.value
        task.result = result
        task.error_message = None
        task.updated_at = datetime.now(timezone.utc)
        self.session.add(task)
        self.session.flush()
        self.session.refresh(task)
        return task

    def mark_failed(self, task: Task, error_message: str) -> Task:
        task.status = TaskStatus.FAILED.value
        task.error_message = error_message
        task.updated_at = datetime.now(timezone.utc)
        self.session.add(task)
        self.session.flush()
        self.session.refresh(task)
        return task

    def save(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
