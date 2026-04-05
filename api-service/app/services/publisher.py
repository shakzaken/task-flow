from __future__ import annotations

import json
import logging
from typing import Protocol
from uuid import UUID

import aio_pika

from app.schemas.task import TaskType

logger = logging.getLogger(__name__)


class Publisher(Protocol):
    async def publish_task_created(self, task_id: UUID, task_type: TaskType) -> None:
        ...


class RabbitMQPublisher:
    def __init__(self, rabbitmq_url: str) -> None:
        self.rabbitmq_url = rabbitmq_url

    async def publish_task_created(self, task_id: UUID, task_type: TaskType) -> None:
        logger.info("Publishing task.created message for task_id=%s task_type=%s", task_id, task_type.value)
        connection = await aio_pika.connect_robust(self.rabbitmq_url)
        channel = await connection.channel()
        exchange = await channel.declare_exchange("tasks", aio_pika.ExchangeType.DIRECT, durable=True)
        queue = await channel.declare_queue("tasks.phase1", durable=True)
        await queue.bind(exchange, routing_key="task.created")
        body = json.dumps({"task_id": str(task_id), "task_type": task_type.value})
        await exchange.publish(
            aio_pika.Message(
                body=body.encode("utf-8"),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key="task.created",
        )
        await channel.close()
        await connection.close()
