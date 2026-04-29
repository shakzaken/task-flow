from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dependencies import build_storage_service
from app.api.middleware import rate_limit_middleware
from app.core.config import Settings, get_settings
from app.api.routes.artifacts import router as artifacts_router
from app.api.routes.frontend import DEFAULT_STATIC_DIR, router as frontend_router
from app.api.routes.health import router as health_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.uploads import router as uploads_router
from app.services.migration_runner import MigrationRunner, build_migration_runner
from app.services.publisher import Publisher, RabbitMQPublisher
from app.services.rate_limiter import NoopRateLimiter, RateLimiter, build_rate_limiter

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    migration_runner: MigrationRunner = app.state.migration_runner
    publisher = RabbitMQPublisher(settings.rabbitmq_url)
    rate_limiter = build_rate_limiter(settings.redis_url, settings.rate_limit_prefix)
    storage_service = build_storage_service(settings)

    logger.info("Starting application startup sequence")

    try:
        logger.info("Running database migrations")
        await migration_runner.run_pending_migrations()
        logger.info("Database migrations completed")

        logger.info("Connecting RabbitMQ publisher to %s", settings.rabbitmq_url)
        await publisher.connect()
        logger.info("RabbitMQ publisher connected")

        logger.info(
            "Ensuring object storage is ready (bucket=%s, endpoint=%s)",
            settings.s3_bucket,
            settings.s3_endpoint or "aws",
        )
        await storage_service.ensure_ready()
        logger.info("Object storage is ready")
    except Exception:
        logger.exception("Application startup failed")
        await storage_service.close()
        await publisher.close()
        await rate_limiter.close()
        raise

    app.state.publisher = publisher
    app.state.rate_limiter = rate_limiter
    app.state.storage_service = storage_service
    try:
        yield
    finally:
        await storage_service.close()
        await publisher.close()
        await rate_limiter.close()


def create_app(
    publisher: Publisher | None = None,
    rate_limiter: RateLimiter | None = None,
    settings: Settings | None = None,
    migration_runner: MigrationRunner | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    app = FastAPI(
        title="Task Flow API Service",
        version="0.1.0",
        lifespan=None if publisher is not None or rate_limiter is not None else lifespan,
    )
    app.state.settings = resolved_settings
    app.state.publisher = publisher or getattr(app.state, "publisher", None)
    app.state.rate_limiter = rate_limiter or NoopRateLimiter()
    app.state.storage_service = build_storage_service(resolved_settings)
    app.state.migration_runner = migration_runner or build_migration_runner(resolved_settings)
    app.state.frontend_static_dir = DEFAULT_STATIC_DIR
    if resolved_settings.cors_allow_all_origins:
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.middleware("http")(rate_limit_middleware)

    app.include_router(health_router)
    app.include_router(artifacts_router)
    app.include_router(tasks_router)
    app.include_router(uploads_router)
    app.include_router(frontend_router)
    return app


app = create_app()
