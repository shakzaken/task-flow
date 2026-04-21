from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_task_service
from app.main import create_app
from app.services.publisher import Publisher
from app.services.rate_limiter import RateLimitResult


class RecordingPublisher(Publisher):
    async def publish_task_created(self, task_id, task_type) -> None:
        return None


class StubRateLimiter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.allowed = True

    async def allow(self, key: str, rule) -> RateLimitResult:
        self.calls.append((key, rule.name))
        return RateLimitResult(
            allowed=self.allowed,
            limit=rule.capacity,
            remaining=0 if not self.allowed else rule.capacity - 1,
            retry_after_seconds=12 if not self.allowed else 0,
        )

    async def close(self) -> None:
        return None


class StubTaskService:
    async def list_recent_tasks(self, limit: int):
        return {"tasks": []}


@pytest.fixture
async def rate_limited_client() -> AsyncGenerator[tuple[AsyncClient, StubRateLimiter], None]:
    limiter = StubRateLimiter()
    app = create_app(publisher=RecordingPublisher(), rate_limiter=limiter)
    app.dependency_overrides[get_task_service] = lambda: StubTaskService()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client, limiter

    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_post_tasks_is_rate_limited_by_ip(rate_limited_client) -> None:
    client, limiter = rate_limited_client
    limiter.allowed = False

    response = await client.post(
        "/tasks",
        headers={"X-Forwarded-For": "203.0.113.10"},
        json={
            "task_type": "send_email",
            "payload": {
                "to": "user@example.com",
                "subject": "Hello",
                "body": "Hi",
            },
        },
    )

    assert response.status_code == 429
    assert response.headers["X-RateLimit-Limit"] == "5"
    assert response.headers["Retry-After"] == "12"
    assert limiter.calls == [("203.0.113.10", "task-create")]


@pytest.mark.anyio
async def test_get_tasks_uses_read_rule(rate_limited_client) -> None:
    client, limiter = rate_limited_client

    response = await client.get("/tasks", headers={"X-Forwarded-For": "198.51.100.20"})

    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == "20"
    assert response.headers["X-RateLimit-Remaining"] == "19"
    assert limiter.calls == [("198.51.100.20", "reads")]


@pytest.mark.anyio
async def test_health_endpoint_skips_rate_limiter(rate_limited_client) -> None:
    client, limiter = rate_limited_client

    response = await client.get("/health")

    assert response.status_code == 200
    assert "X-RateLimit-Limit" not in response.headers
    assert limiter.calls == []
