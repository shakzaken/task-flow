from collections.abc import AsyncGenerator
from functools import lru_cache

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.repositories.task_repository import TaskRepository
from app.db.session import AsyncSessionFactory, get_session_factory
from app.services.publisher import Publisher
from app.services.storage import StorageService
from app.services.task_service import TaskService


@lru_cache
def get_cached_session_factory() -> AsyncSessionFactory:
    settings = get_settings()
    return get_session_factory(settings.database_url)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_cached_session_factory()
    async with session_factory() as session:
        yield session


def get_task_repository(session: AsyncSession = Depends(get_db_session)) -> TaskRepository:
    return TaskRepository(session)


def get_storage_service(settings: Settings = Depends(get_settings)) -> StorageService:
    return StorageService(settings.local_storage_path)


def get_publisher_service(request: Request) -> Publisher:
    return request.app.state.publisher


def get_task_service(
    repository: TaskRepository = Depends(get_task_repository),
    storage: StorageService = Depends(get_storage_service),
    publisher: Publisher = Depends(get_publisher_service),
) -> TaskService:
    return TaskService(repository=repository, storage=storage, publisher=publisher)
