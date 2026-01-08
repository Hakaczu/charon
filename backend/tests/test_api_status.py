from fastapi.testclient import TestClient

from app.main import create_app


def test_status_endpoint():
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "service_time" in data
    assert "version" in data
