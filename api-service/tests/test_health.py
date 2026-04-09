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
async def test_cors_is_not_enabled_without_configured_origins() -> None:
    app = create_app(
        publisher=NoopPublisher(),
        settings=Settings(
            APP_ENVIRONMENT="development",
            CORS_ALLOWED_ORIGINS="",
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


@pytest.mark.anyio
async def test_cors_is_enabled_for_configured_origins() -> None:
    app = create_app(
        publisher=NoopPublisher(),
        settings=Settings(
            APP_ENVIRONMENT="development",
            CORS_ALLOWED_ORIGINS="https://app.example.com",
        ),
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.options(
            "/health",
            headers={
                "Origin": "https://app.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.headers["access-control-allow-origin"] == "https://app.example.com"
