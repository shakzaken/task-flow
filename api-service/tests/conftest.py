from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session, get_storage_service, get_task_service
from app.db.base import Base
from app.db.repositories.task_repository import TaskRepository
from app.db.session import get_engine, get_session_factory
from app.main import create_app
from app.services.publisher import Publisher
from app.services.storage import StorageService
from app.services.task_service import TaskService
from tests.fakes import FakeStorageService


class RecordingPublisher(Publisher):
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    async def publish_task_created(self, task_id, task_type) -> None:
        self.messages.append((str(task_id), task_type.value))


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def session_factory(tmp_path: Path):
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    engine = get_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield get_session_factory(database_url)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


@pytest.fixture
def recording_publisher() -> RecordingPublisher:
    return RecordingPublisher()


@pytest.fixture
def storage_service() -> FakeStorageService:
    return FakeStorageService()


@pytest.fixture
def task_service(
    db_session: AsyncSession,
    storage_service: StorageService,
    recording_publisher: RecordingPublisher,
) -> TaskService:
    repository = TaskRepository(db_session)
    return TaskService(repository=repository, storage=storage_service, publisher=recording_publisher)


@pytest.fixture
async def app_client(
    db_session: AsyncSession,
    task_service: TaskService,
    storage_service: StorageService,
    recording_publisher: RecordingPublisher,
) -> AsyncGenerator[AsyncClient, None]:
    app = create_app(publisher=recording_publisher)

    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_task_service] = lambda: task_service
    app.dependency_overrides[get_storage_service] = lambda: storage_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()
