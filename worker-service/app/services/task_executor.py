from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.orm import sessionmaker

from app.db.repositories.task_repository import TaskRepository
from app.handlers.resize_image import handle_resize_image
from app.handlers.send_email import handle_send_email
from app.schemas import PAYLOAD_TYPE_MAP, TaskType
from app.services.email_sender import EmailSender
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


class TaskExecutor:
    def __init__(
        self,
        session_factory: sessionmaker,
        storage: StorageService,
        email_sender: EmailSender,
        repository_type: type[TaskRepository] = TaskRepository,
    ) -> None:
        self.session_factory = session_factory
        self.storage = storage
        self.email_sender = email_sender
        self.repository_type = repository_type

    def execute(self, task_id: UUID, message_task_type: TaskType) -> bool:
        with self.session_factory() as session:
            repository = self.repository_type(session)
            task = repository.get_task_by_id(task_id)
            if task is None:
                logger.warning("Task row %s was not found during worker execution.", task_id)
                return False

            try:
                repository.mark_processing(task)
                repository.save()

                task_type = task.task_type
                if task_type != message_task_type:
                    logger.warning(
                        "Worker message task type %s did not match stored task type %s for %s.",
                        message_task_type.value,
                        task_type.value,
                        task_id,
                    )

                payload_model = PAYLOAD_TYPE_MAP[task_type].validate_python(task.payload)
                if task_type is TaskType.SEND_EMAIL:
                    result = handle_send_email(payload_model, self.email_sender)
                elif task_type is TaskType.RESIZE_IMAGE:
                    result = handle_resize_image(task.id, payload_model, self.storage)
                else:
                    raise ValueError(f"Unsupported task type: {task_type.value}")

                repository.mark_completed(task, result)
                repository.save()
                return True
            except Exception as exc:
                repository.rollback()
                task = repository.get_task_by_id(task_id)
                if task is not None:
                    repository.mark_failed(task, str(exc))
                    repository.save()
                logger.exception("Task %s failed during worker execution.", task_id)
                return False
