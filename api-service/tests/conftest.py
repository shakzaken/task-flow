from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session, get_publisher_service, get_storage_service, get_task_service
from app.db.base import Base
from app.db.repositories.task_repository import TaskRepository
from app.db.session import get_engine, get_session_factory
from app.main import create_app
from app.services.publisher import Publisher
from app.services.storage import StorageService
from app.services.task_service import TaskService


class RecordingPublisher(Publisher):
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def publish_task_created(self, task_id, task_type) -> None:
        self.messages.append((str(task_id), task_type.value))


@pytest.fixture
def storage_root(tmp_path: Path) -> Path:
    return tmp_path / "shared-storage"


@pytest.fixture
def session_factory(tmp_path: Path):
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    engine = get_engine(database_url)
    Base.metadata.create_all(bind=engine)
    yield get_session_factory(database_url)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(session_factory) -> Generator[Session, None, None]:
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def recording_publisher() -> RecordingPublisher:
    return RecordingPublisher()


@pytest.fixture
def storage_service(storage_root: Path) -> StorageService:
    return StorageService(storage_root)


@pytest.fixture
def task_service(db_session: Session, storage_service: StorageService, recording_publisher: RecordingPublisher) -> TaskService:
    repository = TaskRepository(db_session)
    return TaskService(repository=repository, storage=storage_service, publisher=recording_publisher)


@pytest.fixture
def app_client(db_session: Session, task_service: TaskService, storage_service: StorageService, recording_publisher: RecordingPublisher):
    app = create_app()

    def override_get_db_session():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_task_service] = lambda: task_service
    app.dependency_overrides[get_storage_service] = lambda: storage_service
    app.dependency_overrides[get_publisher_service] = lambda: recording_publisher

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()

