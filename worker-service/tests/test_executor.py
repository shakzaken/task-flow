from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from PIL import Image

from app.db.repositories.task_repository import TaskRepository
from app.schemas import TaskStatus, TaskType
from app.services.task_executor import TaskExecutor


def test_execute_send_email_marks_task_completed(
    repository: TaskRepository,
    task_executor: TaskExecutor,
    seeded_task,
) -> None:
    success = task_executor.execute(seeded_task, TaskType.SEND_EMAIL)

    db_task = repository.get_task_by_id(seeded_task)

    assert success is True
    assert db_task is not None
    assert db_task.status == TaskStatus.COMPLETED.value
    assert db_task.result == {"delivered": True}
    assert db_task.error_message is None


def test_execute_handler_failure_marks_task_failed(
    repository: TaskRepository,
    task_executor: TaskExecutor,
) -> None:
    task_id = uuid4()
    repository.create_task(
        task_id=task_id,
        task_type=TaskType.RESIZE_IMAGE,
        status=TaskStatus.PENDING,
        payload={
            "image_path": "uploads/tasks/missing/input.jpg",
            "width": 100,
            "height": 100,
        },
    )
    repository.save()

    success = task_executor.execute(task_id, TaskType.RESIZE_IMAGE)

    db_task = repository.get_task_by_id(task_id)

    assert success is False
    assert db_task is not None
    assert db_task.status == TaskStatus.FAILED.value
    assert "Input image does not exist" in db_task.error_message


def test_execute_resize_image_writes_output(
    repository: TaskRepository,
    task_executor: TaskExecutor,
    storage_root: Path,
) -> None:
    task_id = uuid4()
    input_relative_path = "uploads/tasks/sample/input.png"
    input_path = storage_root / input_relative_path
    input_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.new("RGB", (10, 10), color="red") as image:
        image.save(input_path, format="PNG")

    repository.create_task(
        task_id=task_id,
        task_type=TaskType.RESIZE_IMAGE,
        status=TaskStatus.PENDING,
        payload={
            "image_path": input_relative_path,
            "width": 4,
            "height": 6,
        },
    )
    repository.save()

    success = task_executor.execute(task_id, TaskType.RESIZE_IMAGE)

    db_task = repository.get_task_by_id(task_id)

    assert success is True
    assert db_task is not None
    assert db_task.status == TaskStatus.COMPLETED.value
    assert db_task.result is not None
    output_path = storage_root / db_task.result["output_path"]
    assert output_path.exists()
    with Image.open(output_path) as output_image:
        assert output_image.size == (4, 6)
