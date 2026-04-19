from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from PIL import Image
from pypdf import PdfReader, PdfWriter

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


def test_execute_merge_pdfs_writes_output(
    repository: TaskRepository,
    task_executor: TaskExecutor,
    storage_root: Path,
) -> None:
    task_id = uuid4()
    first_input_relative_path = "uploads/tasks/sample/input-1.pdf"
    second_input_relative_path = "uploads/tasks/sample/input-2.pdf"
    first_input_path = storage_root / first_input_relative_path
    second_input_path = storage_root / second_input_relative_path
    first_input_path.parent.mkdir(parents=True, exist_ok=True)

    first_writer = PdfWriter()
    first_writer.add_blank_page(width=72, height=72)
    with first_input_path.open("wb") as first_file:
        first_writer.write(first_file)

    second_writer = PdfWriter()
    second_writer.add_blank_page(width=144, height=144)
    second_writer.add_blank_page(width=216, height=216)
    with second_input_path.open("wb") as second_file:
        second_writer.write(second_file)

    repository.create_task(
        task_id=task_id,
        task_type=TaskType.MERGE_PDFS,
        status=TaskStatus.PENDING,
        payload={
            "first_pdf_path": first_input_relative_path,
            "second_pdf_path": second_input_relative_path,
        },
    )
    repository.save()

    success = task_executor.execute(task_id, TaskType.MERGE_PDFS)

    db_task = repository.get_task_by_id(task_id)

    assert success is True
    assert db_task is not None
    assert db_task.status == TaskStatus.COMPLETED.value
    assert db_task.result is not None
    assert db_task.result["page_count"] == 3

    output_path = storage_root / db_task.result["output_path"]
    assert output_path.exists()
    with output_path.open("rb") as output_file:
        reader = PdfReader(output_file)
        assert len(reader.pages) == 3
        assert float(reader.pages[0].mediabox.width) == 72
        assert float(reader.pages[1].mediabox.width) == 144
        assert float(reader.pages[2].mediabox.width) == 216
