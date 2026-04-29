from __future__ import annotations

import json
import logging
from typing import Protocol
from uuid import UUID

import aio_pika
from aio_pika.abc import AbstractChannel, AbstractConnection, AbstractExchange

from app.schemas.task import TaskType

logger = logging.getLogger("uvicorn.error")


class Publisher(Protocol):
    async def publish_task_created(self, task_id: UUID, task_type: TaskType) -> None:
        ...


class RabbitMQPublisher:
    def __init__(self, rabbitmq_url: str) -> None:
        self.rabbitmq_url = rabbitmq_url
        self._connection: AbstractConnection | None = None
        self._channel: AbstractChannel | None = None
        self._exchange: AbstractExchange | None = None

    async def connect(self) -> None:
        if self._connection is not None and not self._connection.is_closed:
            return

        logger.info("Connecting RabbitMQ publisher")
        connection = await aio_pika.connect_robust(self.rabbitmq_url)
        channel = await connection.channel()
        exchange = await channel.declare_exchange("tasks", aio_pika.ExchangeType.DIRECT, durable=True)
        queue = await channel.declare_queue("tasks.phase1", durable=True)
        await queue.bind(exchange, routing_key="task.created")

        self._connection = connection
        self._channel = channel
        self._exchange = exchange

    async def close(self) -> None:
        if self._channel is not None and not self._channel.is_closed:
            await self._channel.close()
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()

        self._channel = None
        self._connection = None
        self._exchange = None

    async def publish_task_created(self, task_id: UUID, task_type: TaskType) -> None:
        if self._exchange is None or self._connection is None or self._connection.is_closed:
            raise RuntimeError("RabbitMQ publisher is not connected")

        logger.info("Publishing task.created message for task_id=%s task_type=%s", task_id, task_type.value)
        body = json.dumps({"task_id": str(task_id), "task_type": task_type.value})
        await self._exchange.publish(
            aio_pika.Message(
                body=body.encode("utf-8"),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key="task.created",
        )
