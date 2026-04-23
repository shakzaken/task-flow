from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dependencies import build_storage_service
from app.api.middleware import rate_limit_middleware
from app.core.config import Settings, get_settings
from app.api.routes.artifacts import router as artifacts_router
from app.api.routes.health import router as health_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.uploads import router as uploads_router
from app.services.publisher import Publisher, RabbitMQPublisher
from app.services.rate_limiter import NoopRateLimiter, RateLimiter, build_rate_limiter


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    publisher = RabbitMQPublisher(settings.rabbitmq_url)
    rate_limiter = build_rate_limiter(settings.redis_url, settings.rate_limit_prefix)
    storage_service = build_storage_service(settings)
    await publisher.connect()
    await storage_service.ensure_ready()
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
    if resolved_settings.cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=resolved_settings.cors_allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.middleware("http")(rate_limit_middleware)

    app.include_router(health_router)
    app.include_router(artifacts_router)
    app.include_router(tasks_router)
    app.include_router(uploads_router)
    return app


app = create_app()
