from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_storage_service, get_task_service
from app.db.base import Base
from app.db.repositories.task_repository import TaskRepository
from app.db.session import get_engine, get_session_factory
from app.main import create_app
from app.schemas.task import CreateTaskRequest, TaskStatus, TaskType
from app.services.publisher import Publisher
from app.services.storage import StorageService
from app.services.task_service import TaskService
from tests.fakes import FakeStorageService, StoredObject


@pytest.mark.anyio
async def test_create_send_email_task(app_client: AsyncClient, recording_publisher: Publisher) -> None:
    response = await app_client.post(
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


@pytest.mark.anyio
async def test_create_resize_image_task(
    app_client: AsyncClient,
    storage_service: StorageService,
    recording_publisher: Publisher,
) -> None:
    upload_response = await app_client.post(
        "/uploads",
        files={"file": ("input.jpg", BytesIO(b"fake-image-bytes"), "image/jpeg")},
    )
    temporary_path = upload_response.json()["path"]

    response = await app_client.post(
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
    assert f"uploads/tasks/{task_id}/input.jpg" in storage_service.objects
    assert temporary_path not in storage_service.objects


@pytest.mark.anyio
async def test_create_merge_pdfs_task(
    app_client: AsyncClient,
    storage_service: StorageService,
    recording_publisher: Publisher,
) -> None:
    first_upload_response = await app_client.post(
        "/uploads",
        files={"file": ("first.pdf", BytesIO(b"%PDF-first"), "application/pdf")},
    )
    second_upload_response = await app_client.post(
        "/uploads",
        files={"file": ("second.pdf", BytesIO(b"%PDF-second"), "application/pdf")},
    )

    response = await app_client.post(
        "/tasks",
        json={
            "task_type": "merge_pdfs",
            "payload": {
                "first_pdf_path": first_upload_response.json()["path"],
                "second_pdf_path": second_upload_response.json()["path"],
            },
        },
    )

    assert response.status_code == 202
    assert response.json()["status"] == "PENDING"
    assert len(recording_publisher.messages) == 1

    task_id = response.json()["task_id"]
    assert f"uploads/tasks/{task_id}/input-1.pdf" in storage_service.objects
    assert f"uploads/tasks/{task_id}/input-2.pdf" in storage_service.objects
    assert first_upload_response.json()["path"] not in storage_service.objects
    assert second_upload_response.json()["path"] not in storage_service.objects


@pytest.mark.anyio
async def test_create_summarize_pdf_task(
    app_client: AsyncClient,
    storage_service: StorageService,
    recording_publisher: Publisher,
) -> None:
    upload_response = await app_client.post(
        "/uploads",
        files={"file": ("report.pdf", BytesIO(b"%PDF-report"), "application/pdf")},
    )
    temporary_path = upload_response.json()["path"]

    response = await app_client.post(
        "/tasks",
        json={
            "task_type": "summarize_pdf",
            "payload": {
                "pdf_path": temporary_path,
            },
        },
    )

    assert response.status_code == 202
    assert response.json()["status"] == "PENDING"
    assert len(recording_publisher.messages) == 1

    task_id = response.json()["task_id"]
    assert f"uploads/tasks/{task_id}/input.pdf" in storage_service.objects
    assert temporary_path not in storage_service.objects


@pytest.mark.anyio
async def test_rejects_unsupported_task_type(app_client: AsyncClient) -> None:
    response = await app_client.post(
        "/tasks",
        json={
            "task_type": "unknown",
            "payload": {},
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_rejects_invalid_payload_shape(app_client: AsyncClient) -> None:
    response = await app_client.post(
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


@pytest.mark.anyio
async def test_fetch_existing_task(app_client: AsyncClient) -> None:
    create_response = await app_client.post(
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

    response = await app_client.get(f"/tasks/{task_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == task_id
    assert body["type"] == "send_email"
    assert body["status"] == "PENDING"


@pytest.mark.anyio
async def test_list_recent_tasks_returns_newest_first(app_client: AsyncClient) -> None:
    first_response = await app_client.post(
        "/tasks",
        json={
            "task_type": "send_email",
            "payload": {
                "to": "first@example.com",
                "subject": "First",
                "body": "First body",
            },
        },
    )
    second_response = await app_client.post(
        "/tasks",
        json={
            "task_type": "send_email",
            "payload": {
                "to": "second@example.com",
                "subject": "Second",
                "body": "Second body",
            },
        },
    )

    response = await app_client.get("/tasks?limit=10")

    assert response.status_code == 200
    body = response.json()
    assert [task["id"] for task in body["tasks"][:2]] == [
        second_response.json()["task_id"],
        first_response.json()["task_id"],
    ]


@pytest.mark.anyio
async def test_missing_task_returns_404(app_client: AsyncClient) -> None:
    response = await app_client.get("/tasks/314d4dc8-31f8-44c9-b8a5-648370d4d40b")

    assert response.status_code == 404


class CheckingPublisher(Publisher):
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.row_was_visible_during_publish = False

    async def publish_task_created(self, task_id, task_type) -> None:
        async with get_session_factory(self.database_url)() as session:
            repository = TaskRepository(session)
            self.row_was_visible_during_publish = await repository.get_task_by_id(task_id) is not None


@pytest.mark.anyio
async def test_task_row_is_created_before_publish_completes(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'publish-check.db'}"
    engine = get_engine(database_url)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with get_session_factory(database_url)() as session:
        storage = FakeStorageService()
        publisher = CheckingPublisher(database_url)
        service = TaskService(repository=TaskRepository(session), storage=storage, publisher=publisher)

        response = await service.create_task(
            CreateTaskRequest(
                task_type=TaskType.SEND_EMAIL,
                payload={"to": "user@example.com", "subject": "Hi", "body": "Hello"},
            )
        )

    assert response.status == TaskStatus.PENDING
    assert publisher.row_was_visible_during_publish is True
    await engine.dispose()


@pytest.mark.anyio
async def test_routes_delegate_to_service_via_dependency_override() -> None:
    class StubTaskService:
        def __init__(self) -> None:
            self.create_called = False
            self.get_called = False

        async def create_task(self, request):
            self.create_called = True
            return {"task_id": "3f7d37dd-b4b0-4996-8f7a-4c8374b9cb5d", "status": "PENDING"}

        async def get_task(self, task_id):
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

        async def list_recent_tasks(self, limit):
            return {
                "tasks": [
                    {
                        "id": "53ae8720-ae79-4480-b984-b4fbdcfc8838",
                        "type": "send_email",
                        "status": "PENDING",
                        "payload": {},
                        "result": None,
                        "error_message": None,
                        "created_at": "2026-01-01T00:00:00Z",
                        "updated_at": "2026-01-01T00:00:00Z",
                    }
                ]
            }

    stub = StubTaskService()
    app = create_app(publisher=stub)
    app.dependency_overrides[get_task_service] = lambda: stub

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        create_response = await client.post(
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
        read_response = await client.get("/tasks/53ae8720-ae79-4480-b984-b4fbdcfc8838")
        list_response = await client.get("/tasks?limit=10")

    assert create_response.status_code == 202
    assert read_response.status_code == 200
    assert list_response.status_code == 200
    assert stub.create_called is True
    assert stub.get_called is True


@pytest.mark.anyio
async def test_dependency_injected_services_can_be_replaced_in_tests(tmp_path: Path) -> None:
    class NoopPublisher(Publisher):
        async def publish_task_created(self, task_id, task_type) -> None:
            return None

    app = create_app(publisher=NoopPublisher())

    class CheckingStorageService(FakeStorageService):
        def __init__(self) -> None:
            super().__init__()
            self.store_called = False

        async def store_temporary_upload(self, upload_file):
            self.store_called = True
            return await super().store_temporary_upload(upload_file)

    fake_storage = CheckingStorageService()
    app.dependency_overrides[get_storage_service] = lambda: fake_storage

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.post(
            "/uploads",
            files={"file": ("demo.txt", BytesIO(b"hello"), "text/plain")},
        )

    assert response.status_code == 201
    assert fake_storage.store_called is True


@pytest.mark.anyio
async def test_upload_file_returns_storage_path(app_client: AsyncClient) -> None:
    response = await app_client.post(
        "/uploads",
        files={"file": ("demo.txt", BytesIO(b"hello"), "text/plain")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["path"].startswith("uploads/tmp/")
    assert body["filename"] == "demo.txt"


@pytest.mark.anyio
async def test_resize_image_task_stores_relative_path(app_client: AsyncClient) -> None:
    upload_response = await app_client.post(
        "/uploads",
        files={"file": ("input.png", BytesIO(b"pngdata"), "image/png")},
    )
    temporary_path = upload_response.json()["path"]

    create_response = await app_client.post(
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

    read_response = await app_client.get(f"/tasks/{task_id}")
    assert read_response.status_code == 200
    assert read_response.json()["payload"]["image_path"] == f"uploads/tasks/{task_id}/input.png"


@pytest.mark.anyio
async def test_merge_pdfs_task_stores_relative_paths(app_client: AsyncClient) -> None:
    first_upload_response = await app_client.post(
        "/uploads",
        files={"file": ("first.pdf", BytesIO(b"%PDF-first"), "application/pdf")},
    )
    second_upload_response = await app_client.post(
        "/uploads",
        files={"file": ("second.pdf", BytesIO(b"%PDF-second"), "application/pdf")},
    )

    create_response = await app_client.post(
        "/tasks",
        json={
            "task_type": "merge_pdfs",
            "payload": {
                "first_pdf_path": first_upload_response.json()["path"],
                "second_pdf_path": second_upload_response.json()["path"],
            },
        },
    )
    task_id = create_response.json()["task_id"]

    read_response = await app_client.get(f"/tasks/{task_id}")
    assert read_response.status_code == 200
    assert read_response.json()["payload"]["first_pdf_path"] == f"uploads/tasks/{task_id}/input-1.pdf"
    assert read_response.json()["payload"]["second_pdf_path"] == f"uploads/tasks/{task_id}/input-2.pdf"


@pytest.mark.anyio
async def test_summarize_pdf_task_stores_relative_path(app_client: AsyncClient) -> None:
    upload_response = await app_client.post(
        "/uploads",
        files={"file": ("report.pdf", BytesIO(b"%PDF-report"), "application/pdf")},
    )

    create_response = await app_client.post(
        "/tasks",
        json={
            "task_type": "summarize_pdf",
            "payload": {
                "pdf_path": upload_response.json()["path"],
            },
        },
    )
    task_id = create_response.json()["task_id"]

    read_response = await app_client.get(f"/tasks/{task_id}")
    assert read_response.status_code == 200
    assert read_response.json()["payload"]["pdf_path"] == f"uploads/tasks/{task_id}/input.pdf"


@pytest.mark.anyio
async def test_cleanup_stale_temporary_uploads(storage_service: StorageService) -> None:
    storage_service.objects["uploads/tmp/stale.txt"] = StoredObject(
        body=b"stale",
        last_modified=datetime.fromtimestamp(0, tz=timezone.utc),
        content_type="text/plain",
    )

    deleted = await storage_service.cleanup_stale_uploads(ttl_seconds=0)

    assert "uploads/tmp/stale.txt" in deleted
    assert "uploads/tmp/stale.txt" not in storage_service.objects


@pytest.mark.anyio
async def test_artifact_download_returns_output_file(app_client: AsyncClient, storage_service: StorageService) -> None:
    storage_service.objects["outputs/task-1/output.png"] = StoredObject(
        body=b"fake-image",
        last_modified=datetime.now(timezone.utc),
        content_type="image/png",
    )

    response = await app_client.get("/artifacts/outputs/task-1/output.png")

    assert response.status_code == 200
    assert response.content == b"fake-image"


@pytest.mark.anyio
async def test_missing_artifact_returns_404(app_client: AsyncClient) -> None:
    response = await app_client.get("/artifacts/outputs/missing.png")

    assert response.status_code == 404
