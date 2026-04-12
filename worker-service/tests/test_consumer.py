from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from app.consumers.task_consumer import RabbitMQTaskConsumer
from app.schemas import TaskType


class RecordingExecutor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def execute(self, task_id, task_type) -> bool:
        self.calls.append((str(task_id), task_type.value))
        return True


class FakeIncomingMessage:
    def __init__(self, body: bytes) -> None:
        self.body = body
        self.acked = False
        self.rejected = False
        self.requeue: bool | None = None

    async def ack(self) -> None:
        self.acked = True

    async def reject(self, requeue: bool = False) -> None:
        self.rejected = True
        self.requeue = requeue


def test_parse_message_returns_none_for_invalid_json() -> None:
    assert RabbitMQTaskConsumer._parse_message(b"not-json") is None


def test_parse_message_returns_typed_message() -> None:
    task_id = uuid4()

    parsed = RabbitMQTaskConsumer._parse_message(
        f'{{"task_id":"{task_id}","task_type":"send_email"}}'.encode("utf-8")
    )

    assert parsed is not None
    assert parsed.task_id == task_id
    assert parsed.task_type is TaskType.SEND_EMAIL


@pytest.mark.anyio
async def test_on_message_rejects_malformed_message() -> None:
    consumer = RabbitMQTaskConsumer(
        rabbitmq_url="amqp://guest:guest@localhost:5672/%2F",
        queue_name="tasks.phase1",
        prefetch_count=2,
        task_executor=RecordingExecutor(),
        thread_pool=ThreadPoolExecutor(max_workers=2),
    )
    message = FakeIncomingMessage(b'{"task_id":"missing-task-type"}')

    try:
        await consumer._on_message(message)
    finally:
        consumer.thread_pool.shutdown(wait=True)

    assert message.rejected is True
    assert message.requeue is False
    assert message.acked is False


@pytest.mark.anyio
async def test_on_message_executes_task_and_acks() -> None:
    task_id = uuid4()
    executor = RecordingExecutor()
    consumer = RabbitMQTaskConsumer(
        rabbitmq_url="amqp://guest:guest@localhost:5672/%2F",
        queue_name="tasks.phase1",
        prefetch_count=2,
        task_executor=executor,
        thread_pool=ThreadPoolExecutor(max_workers=2),
    )
    message = FakeIncomingMessage(
        f'{{"task_id":"{task_id}","task_type":"send_email"}}'.encode("utf-8")
    )

    try:
        await consumer._on_message(message)
    finally:
        consumer.thread_pool.shutdown(wait=True)

    assert executor.calls == [(str(task_id), "send_email")]
    assert message.acked is True
    assert message.rejected is False
