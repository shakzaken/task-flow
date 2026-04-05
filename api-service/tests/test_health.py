import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_get_health_returns_ok(app_client: AsyncClient) -> None:
    response = await app_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

