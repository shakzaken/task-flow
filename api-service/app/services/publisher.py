from __future__ import annotations

import json
import logging
from typing import Protocol
from uuid import UUID

import pika

from app.schemas.task import TaskType

logger = logging.getLogger(__name__)


class Publisher(Protocol):
    def publish_task_created(self, task_id: UUID, task_type: TaskType) -> None:
        ...


class RabbitMQPublisher:
    def __init__(self, rabbitmq_url: str) -> None:
        self.rabbitmq_url = rabbitmq_url

    def publish_task_created(self, task_id: UUID, task_type: TaskType) -> None:
        logger.info("Publishing task.created message for task_id=%s task_type=%s", task_id, task_type.value)
        parameters = pika.URLParameters(self.rabbitmq_url)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.exchange_declare(exchange="tasks", exchange_type="direct", durable=True)
        channel.queue_declare(queue="tasks.phase1", durable=True)
        channel.queue_bind(queue="tasks.phase1", exchange="tasks", routing_key="task.created")
        body = json.dumps({"task_id": str(task_id), "task_type": task_type.value})
        channel.basic_publish(
            exchange="tasks",
            routing_key="task.created",
            body=body,
            properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
        )
        connection.close()

