from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.dependencies import get_storage_service, get_task_service
from app.db.repositories.task_repository import TaskRepository
from app.db.session import get_engine, get_session_factory
from app.main import create_app
from app.schemas.task import CreateTaskRequest, TaskStatus, TaskType
from app.services.publisher import Publisher
from app.services.storage import StorageService
from app.services.task_service import TaskService


def test_create_send_email_task(app_client: TestClient, recording_publisher: Publisher) -> None:
    response = app_client.post(
        "/tasks",
        json={
            "task_type": "send_email",
            "payload": {
                "to": "user@example.com",
                "subject": "Welcome",
                "body": "Hello",
            },
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "PENDING"
    assert len(recording_publisher.messages) == 1
    assert recording_publisher.messages[0][1] == "send_email"


def test_create_resize_image_task(app_client: TestClient, storage_service: StorageService, recording_publisher: Publisher) -> None:
    upload_response = app_client.post(
        "/uploads",
        files={"file": ("input.jpg", BytesIO(b"fake-image-bytes"), "image/jpeg")},
    )
    temporary_path = upload_response.json()["path"]

    response = app_client.post(
        "/tasks",
        json={
            "task_type": "resize_image",
            "payload": {
                "image_path": temporary_path,
                "width": 300,
                "height": 200,
            },
        },
    )

    assert response.status_code == 202
    assert response.json()["status"] == "PENDING"
    assert len(recording_publisher.messages) == 1

    task_id = response.json()["task_id"]
    attached_path = storage_service.resolve_relative_path(f"uploads/tasks/{task_id}/input.jpg")
    assert attached_path.exists()
    assert not storage_service.resolve_relative_path(temporary_path).exists()


def test_rejects_unsupported_task_type(app_client: TestClient) -> None:
    response = app_client.post(
        "/tasks",
        json={
            "task_type": "unknown",
            "payload": {},
        },
    )

    assert response.status_code == 422


def test_rejects_invalid_payload_shape(app_client: TestClient) -> None:
    response = app_client.post(
        "/tasks",
        json={
            "task_type": "send_email",
            "payload": {
                "to": "not-an-email",
                "subject": "",
                "body": "",
            },
        },
    )

    assert response.status_code == 422


def test_fetch_existing_task(app_client: TestClient) -> None:
    create_response = app_client.post(
        "/tasks",
        json={
            "task_type": "send_email",
            "payload": {
                "to": "user@example.com",
                "subject": "Subject",
                "body": "Body",
            },
        },
    )
    task_id = create_response.json()["task_id"]

    response = app_client.get(f"/tasks/{task_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == task_id
    assert body["type"] == "send_email"
    assert body["status"] == "PENDING"


def test_missing_task_returns_404(app_client: TestClient) -> None:
    response = app_client.get("/tasks/314d4dc8-31f8-44c9-b8a5-648370d4d40b")

    assert response.status_code == 404


class CheckingPublisher(Publisher):
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.row_was_visible_during_publish = False

    def publish_task_created(self, task_id, task_type) -> None:
        session = get_session_factory(self.database_url)()
        try:
            repository = TaskRepository(session)
            self.row_was_visible_during_publish = repository.get_task_by_id(task_id) is not None
        finally:
            session.close()


def test_task_row_is_created_before_publish_completes(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'publish-check.db'}"
    engine = get_engine(database_url)
    from app.db.base import Base

    Base.metadata.create_all(bind=engine)

    session = get_session_factory(database_url)()
    storage = StorageService(tmp_path / "storage")
    publisher = CheckingPublisher(database_url)
    service = TaskService(repository=TaskRepository(session), storage=storage, publisher=publisher)

    response = service.create_task(
        CreateTaskRequest(
            task_type=TaskType.SEND_EMAIL,
            payload={"to": "user@example.com", "subject": "Hi", "body": "Hello"},
        )
    )

    assert response.status == TaskStatus.PENDING
    assert publisher.row_was_visible_during_publish is True
    session.close()


def test_routes_delegate_to_service_via_dependency_override(tmp_path: Path) -> None:
    class StubTaskService:
        def __init__(self) -> None:
            self.create_called = False
            self.get_called = False

        def create_task(self, request):
            self.create_called = True
            return {"task_id": "3f7d37dd-b4b0-4996-8f7a-4c8374b9cb5d", "status": "PENDING"}

        def get_task(self, task_id):
            self.get_called = True
            return {
                "id": str(task_id),
                "type": "send_email",
                "status": "PENDING",
                "payload": {},
                "result": None,
                "error_message": None,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            }

    stub = StubTaskService()
    app = create_app()
    app.dependency_overrides[get_task_service] = lambda: stub

    with TestClient(app) as client:
        create_response = client.post(
            "/tasks",
            json={
                "task_type": "send_email",
                "payload": {
                    "to": "user@example.com",
                    "subject": "Hi",
                    "body": "Hello",
                },
            },
        )
        read_response = client.get("/tasks/53ae8720-ae79-4480-b984-b4fbdcfc8838")

    assert create_response.status_code == 202
    assert read_response.status_code == 200
    assert stub.create_called is True
    assert stub.get_called is True


def test_dependency_injected_services_can_be_replaced_in_tests(tmp_path: Path) -> None:
    app = create_app()

    class FakeStorageService(StorageService):
        def __init__(self, root_path: Path) -> None:
            super().__init__(root_path)
            self.store_called = False

        def store_temporary_upload(self, upload_file):
            self.store_called = True
            return super().store_temporary_upload(upload_file)

    fake_storage = FakeStorageService(tmp_path / "storage")
    app.dependency_overrides[get_storage_service] = lambda: fake_storage

    with TestClient(app) as client:
        response = client.post(
            "/uploads",
            files={"file": ("demo.txt", BytesIO(b"hello"), "text/plain")},
        )

    assert response.status_code == 201
    assert fake_storage.store_called is True


def test_upload_file_returns_storage_path(app_client: TestClient) -> None:
    response = app_client.post(
        "/uploads",
        files={"file": ("demo.txt", BytesIO(b"hello"), "text/plain")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["path"].startswith("uploads/tmp/")
    assert body["filename"] == "demo.txt"


def test_resize_image_task_stores_relative_path(app_client: TestClient) -> None:
    upload_response = app_client.post(
        "/uploads",
        files={"file": ("input.png", BytesIO(b"pngdata"), "image/png")},
    )
    temporary_path = upload_response.json()["path"]

    create_response = app_client.post(
        "/tasks",
        json={
            "task_type": "resize_image",
            "payload": {
                "image_path": temporary_path,
                "width": 100,
                "height": 100,
            },
        },
    )
    task_id = create_response.json()["task_id"]

    read_response = app_client.get(f"/tasks/{task_id}")
    assert read_response.status_code == 200
    assert read_response.json()["payload"]["image_path"] == f"uploads/tasks/{task_id}/input.png"


def test_cleanup_stale_temporary_uploads(storage_service: StorageService) -> None:
    uploads_root = storage_service.resolve_relative_path("uploads/tmp")
    uploads_root.mkdir(parents=True, exist_ok=True)
    stale_file = uploads_root / "stale.txt"
    stale_file.write_text("stale", encoding="utf-8")

    deleted = storage_service.cleanup_stale_uploads(ttl_seconds=0)

    assert "uploads/tmp/stale.txt" in deleted
    assert not stale_file.exists()
