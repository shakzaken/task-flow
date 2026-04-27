from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
def static_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "static"
    assets_dir = directory / "assets"
    assets_dir.mkdir(parents=True)
    (directory / "index.html").write_text("<html><body>Task Flow UI</body></html>", encoding="utf-8")
    (assets_dir / "app.js").write_text("console.log('task-flow');", encoding="utf-8")
    return directory


@pytest.fixture
async def frontend_client(static_dir: Path):
    app = create_app(publisher=None)
    app.state.frontend_static_dir = static_dir
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client


@pytest.mark.anyio
async def test_serves_frontend_index(frontend_client: AsyncClient) -> None:
    response = await frontend_client.get("/")

    assert response.status_code == 200
    assert "Task Flow UI" in response.text
    assert response.headers["content-type"].startswith("text/html")


@pytest.mark.anyio
async def test_serves_static_asset(frontend_client: AsyncClient) -> None:
    response = await frontend_client.get("/assets/app.js")

    assert response.status_code == 200
    assert response.text == "console.log('task-flow');"


@pytest.mark.anyio
async def test_unknown_frontend_route_returns_index(frontend_client: AsyncClient) -> None:
    response = await frontend_client.get("/dashboard/tasks")

    assert response.status_code == 200
    assert "Task Flow UI" in response.text


@pytest.mark.anyio
async def test_api_prefixed_unknown_route_does_not_return_frontend(frontend_client: AsyncClient) -> None:
    response = await frontend_client.get("/uploads/missing")

    assert response.status_code == 404
    assert "Task Flow UI" not in response.text


@pytest.mark.anyio
async def test_missing_frontend_build_returns_clear_404(tmp_path: Path) -> None:
    app = create_app(publisher=None)
    app.state.frontend_static_dir = tmp_path / "missing-static"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/")

    assert response.status_code == 404
    assert response.json()["detail"] == "Frontend build was not found. Run scripts/build_frontend_for_api.sh first."
