from fastapi.testclient import TestClient


def test_get_health_returns_ok(app_client: TestClient) -> None:
    response = app_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

