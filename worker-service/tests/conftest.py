from __future__ import annotations

import shutil
import tempfile
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
from app.services.pdf_summary import PdfSummaryService
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


class FakeStorageService(StorageService):
    def __init__(self, tmp_path: Path) -> None:
        self.bucket = "test-bucket"
        self.region = "us-east-1"
        self.output_root = "outputs"
        self.work_root = tmp_path / "worker-work"
        self.objects: dict[str, bytes] = {}

    def ensure_ready(self) -> None:
        return None

    def close(self) -> None:
        return None

    def task_workspace(self, task_id: UUID):
        self.work_root.mkdir(parents=True, exist_ok=True)
        workspace = Path(tempfile.mkdtemp(prefix=f"{task_id}-", dir=self.work_root))

        class _WorkspaceContext:
            def __enter__(self_nonlocal) -> Path:
                return workspace

            def __exit__(self_nonlocal, exc_type, exc, tb) -> None:
                shutil.rmtree(workspace, ignore_errors=True)

        return _WorkspaceContext()

    def download_to_path(self, relative_path: str, destination: Path) -> Path:
        key = self.normalize_key(relative_path)
        if key not in self.objects:
            raise FileNotFoundError(f"Input artifact does not exist: {relative_path}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(self.objects[key])
        return destination

    def upload_file(self, source_path: Path, relative_path: str, content_type: str | None = None) -> str:
        key = self.normalize_key(relative_path)
        self.objects[key] = source_path.read_bytes()
        return key

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
def storage_service(tmp_path: Path) -> FakeStorageService:
    return FakeStorageService(tmp_path)


@pytest.fixture
def email_sender() -> FakeEmailSender:
    return FakeEmailSender()


class FakePdfSummaryService(PdfSummaryService):
    def summarize_document(self, text: str) -> dict[str, str]:
        return {
            "summary": f"Summary: {text[:60]}",
            "model": "openrouter/free",
        }


@pytest.fixture
def pdf_summary_service() -> FakePdfSummaryService:
    return FakePdfSummaryService()


@pytest.fixture
def task_executor(
    session_factory,
    storage_service: StorageService,
    email_sender: FakeEmailSender,
    pdf_summary_service: FakePdfSummaryService,
) -> TaskExecutor:
    return TaskExecutor(
        session_factory=session_factory,
        storage=storage_service,
        email_sender=email_sender,
        pdf_summary_service=pdf_summary_service,
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
