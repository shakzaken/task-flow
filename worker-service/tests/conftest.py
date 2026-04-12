from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.base import Base
from app.db.repositories.task_repository import TaskRepository
from app.db.session import get_engine, get_session_factory
from app.main import create_app
from app.schemas import TaskStatus, TaskType
from app.services.email_sender import FakeEmailSender
from app.services.storage import StorageService
from app.services.task_executor import TaskExecutor


class StubConsumer:
    def __init__(self) -> None:
        self.started = False
        self.closed = False

    async def start(self) -> None:
        self.started = True

    async def close(self) -> None:
        self.closed = True


@pytest.fixture
def storage_root(tmp_path: Path) -> Path:
    return tmp_path / "shared-storage"


@pytest.fixture
def database_url(tmp_path: Path) -> str:
    return f"sqlite:///{tmp_path / 'worker.db'}"


@pytest.fixture
def session_factory(database_url: str):
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)

    yield get_session_factory(database_url)

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(session_factory) -> Generator[Session, None, None]:
    with session_factory() as session:
        yield session


@pytest.fixture
def repository(db_session: Session) -> TaskRepository:
    return TaskRepository(db_session)


@pytest.fixture
def storage_service(storage_root: Path) -> StorageService:
    return StorageService(storage_root)


@pytest.fixture
def email_sender() -> FakeEmailSender:
    return FakeEmailSender()


@pytest.fixture
def task_executor(session_factory, storage_service: StorageService, email_sender: FakeEmailSender) -> TaskExecutor:
    return TaskExecutor(
        session_factory=session_factory,
        storage=storage_service,
        email_sender=email_sender,
    )


@pytest.fixture
def seeded_task(repository: TaskRepository) -> UUID:
    task_id = uuid4()
    repository.create_task(
        task_id=task_id,
        task_type=TaskType.SEND_EMAIL,
        status=TaskStatus.PENDING,
        payload={
            "to": "user@example.com",
            "subject": "Welcome",
            "body": "Hello",
        },
    )
    repository.save()
    return task_id


@pytest.fixture
def app_client() -> Generator[TestClient, None, None]:
    settings = Settings(DATABASE_URL="sqlite:///unused.db")
    consumer = StubConsumer()
    app = create_app(consumer=consumer, settings=settings)

    with TestClient(app) as client:
        yield client
