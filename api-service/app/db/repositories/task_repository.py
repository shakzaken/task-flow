from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.task import Task
from app.schemas.task import TaskStatus, TaskType


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_task(
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
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def get_task_by_id(self, task_id: UUID) -> Task | None:
        return await self.session.get(Task, task_id)

    async def save(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def touch(self, task: Task) -> Task:
        task.updated_at = datetime.now(timezone.utc)
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task
