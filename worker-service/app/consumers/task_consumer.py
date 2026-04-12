from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from concurrent.futures import Executor
from uuid import UUID

import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from pydantic import BaseModel, ValidationError

from app.schemas import TaskType
from app.services.task_executor import TaskExecutor

logger = logging.getLogger(__name__)


class TaskMessage(BaseModel):
    task_id: UUID
    task_type: TaskType


class TaskConsumer(ABC):
    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError


class RabbitMQTaskConsumer(TaskConsumer):
    def __init__(
        self,
        rabbitmq_url: str,
        queue_name: str,
        prefetch_count: int,
        task_executor: TaskExecutor,
        thread_pool: Executor,
    ) -> None:
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.prefetch_count = prefetch_count
        self.task_executor = task_executor
        self.thread_pool = thread_pool
        self.connection: aio_pika.abc.AbstractRobustConnection | None = None
        self.channel: aio_pika.abc.AbstractChannel | None = None
        self.queue: aio_pika.abc.AbstractQueue | None = None
        self.consumer_tag: str | None = None

    async def start(self) -> None:
        self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=self.prefetch_count)
        exchange = await self.channel.declare_exchange("tasks", aio_pika.ExchangeType.DIRECT, durable=True)
        self.queue = await self.channel.declare_queue(self.queue_name, durable=True)
        await self.queue.bind(exchange, routing_key="task.created")
        self.consumer_tag = await self.queue.consume(self._on_message)

    async def close(self) -> None:
        if self.queue is not None and self.consumer_tag is not None:
            await self.queue.cancel(self.consumer_tag)
        if self.channel is not None and not self.channel.is_closed:
            await self.channel.close()
        if self.connection is not None and not self.connection.is_closed:
            await self.connection.close()

    async def _on_message(self, message: AbstractIncomingMessage) -> None:
        parsed = self._parse_message(message.body)
        if parsed is None:
            logger.warning("Worker rejected malformed message: %s", message.body.decode("utf-8", errors="ignore"))
            await message.reject(requeue=False)
            return

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            self.thread_pool,
            self.task_executor.execute,
            parsed.task_id,
            parsed.task_type,
        )
        await message.ack()

    @staticmethod
    def _parse_message(body: bytes) -> TaskMessage | None:
        try:
            raw_data = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None

        try:
            return TaskMessage.model_validate(raw_data)
        except ValidationError:
            return None
