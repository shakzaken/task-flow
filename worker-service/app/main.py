from __future__ import annotations

from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.consumers.task_consumer import RabbitMQTaskConsumer, TaskConsumer
from app.core.config import Settings, get_settings
from app.db.session import get_session_factory
from app.services.email_sender import build_email_sender
from app.services.storage import StorageService
from app.services.task_executor import TaskExecutor


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    thread_pool = ThreadPoolExecutor(
        max_workers=settings.worker_max_concurrency,
        thread_name_prefix="worker-task",
    )
    session_factory = get_session_factory(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
    )
    storage = StorageService(settings.local_storage_path, settings.output_storage_path)
    email_sender = build_email_sender(
        mode=settings.email_provider_mode,
        resend_api_key=settings.resend_api_key,
        resend_from_email=settings.resend_from_email,
        resend_from_name=settings.resend_from_name,
    )
    task_executor = TaskExecutor(
        session_factory=session_factory,
        storage=storage,
        email_sender=email_sender,
    )
    consumer: TaskConsumer = RabbitMQTaskConsumer(
        rabbitmq_url=settings.rabbitmq_url,
        queue_name=settings.worker_consumer_queue,
        prefetch_count=settings.rabbitmq_prefetch_count,
        task_executor=task_executor,
        thread_pool=thread_pool,
    )

    app.state.thread_pool = thread_pool
    app.state.consumer = consumer
    try:
        await consumer.start()
        yield
    finally:
        await consumer.close()
        thread_pool.shutdown(wait=True)


def create_app(
    consumer: TaskConsumer | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    app = FastAPI(
        title="Task Flow Worker Service",
        version="0.1.0",
        lifespan=None if consumer is not None else lifespan,
    )
    app.state.settings = resolved_settings
    if consumer is not None:
        app.state.consumer = consumer
    app.include_router(health_router)
    return app


app = create_app()
