import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app
from app.services.publisher import Publisher


class NoopPublisher(Publisher):
    async def publish_task_created(self, task_id, task_type) -> None:
        return None


@pytest.mark.anyio
async def test_get_health_returns_ok(app_client: AsyncClient) -> None:
    response = await app_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_request_logging_records_health_requests(
    app_client: AsyncClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level("INFO", logger="app.request"):
        response = await app_client.get("/health", headers={"Origin": "http://127.0.0.1:4173"})

    assert response.status_code == 200
    assert "GET /health -> 200 origin=http://127.0.0.1:4173" in caplog.text


@pytest.mark.anyio
async def test_cors_allows_all_origins_by_default_in_development() -> None:
    app = create_app(
        publisher=NoopPublisher(),
        settings=Settings(
            APP_ENVIRONMENT="development",
            POSTGRES_HOST="localhost",
        ),
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://127.0.0.1:4173",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.headers["access-control-allow-origin"] == "*"


@pytest.mark.anyio
async def test_cors_is_not_enabled_by_default_in_docker_like_development() -> None:
    app = create_app(
        publisher=NoopPublisher(),
        settings=Settings(
            APP_ENVIRONMENT="development",
            POSTGRES_HOST="postgres",
        ),
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://127.0.0.1:4173",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert "access-control-allow-origin" not in response.headers


@pytest.mark.anyio
async def test_cors_is_not_enabled_by_default_outside_development() -> None:
    app = create_app(
        publisher=NoopPublisher(),
        settings=Settings(
            APP_ENVIRONMENT="production",
        ),
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert "access-control-allow-origin" not in response.headers
