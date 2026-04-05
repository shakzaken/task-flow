from collections.abc import Generator
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.repositories.task_repository import TaskRepository
from app.db.session import SessionFactory, get_session_factory
from app.services.publisher import Publisher, RabbitMQPublisher
from app.services.storage import StorageService
from app.services.task_service import TaskService


@lru_cache
def get_cached_session_factory() -> SessionFactory:
    settings = get_settings()
    return get_session_factory(settings.database_url)


def get_db_session() -> Generator[Session, None, None]:
    session_factory = get_cached_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def get_task_repository(session: Session = Depends(get_db_session)) -> TaskRepository:
    return TaskRepository(session)


def get_storage_service(settings: Settings = Depends(get_settings)) -> StorageService:
    return StorageService(settings.local_storage_path)


def get_publisher_service(settings: Settings = Depends(get_settings)) -> Publisher:
    return RabbitMQPublisher(settings.rabbitmq_url)


def get_task_service(
    repository: TaskRepository = Depends(get_task_repository),
    storage: StorageService = Depends(get_storage_service),
    publisher: Publisher = Depends(get_publisher_service),
) -> TaskService:
    return TaskService(repository=repository, storage=storage, publisher=publisher)

