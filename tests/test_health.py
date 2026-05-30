from fastapi.testclient import TestClient


def test_health_returns_200():
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200


def test_health_body():
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "zdailyscan"
