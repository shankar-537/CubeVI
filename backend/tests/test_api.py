import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.cube.serialization import state_from_faces


@pytest.fixture
def client():
    return TestClient(app)


def test_health_route(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_scramble_route_default(client):
    response = client.get("/api/scramble")
    assert response.status_code == 200
    data = response.json()
    assert "scramble" in data
    assert "faces" in data
    assert len(data["scramble"]) == 6

    # Verify that the returned faces represent a valid cube state
    state = state_from_faces(data["faces"])
    assert state.is_valid()


def test_scramble_route_custom_length(client):
    response = client.get("/api/scramble?length=12")
    assert response.status_code == 200
    data = response.json()
    assert len(data["scramble"]) == 12

    state = state_from_faces(data["faces"])
    assert state.is_valid()


def test_scramble_route_invalid_length(client):
    response = client.get("/api/scramble?length=0")
    assert response.status_code == 400
    assert "Length of scramble must be positive" in response.json()["detail"]
