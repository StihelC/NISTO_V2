"""Device API tests."""

from __future__ import annotations

from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.db import Base, engine


@pytest.fixture(autouse=True)
def reset_db() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_device_crud_happy_path(client: TestClient) -> None:
    response = client.post(
        "/api/devices",
        json={"name": "Router A", "type": "router", "config": {"os": "ios"}},
    )
    assert response.status_code == 201
    device = response.json()
    assert device["name"] == "Router A"
    device_id = device["id"]

    list_response = client.get("/api/devices")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = client.put(
        f"/api/devices/{device_id}",
        json={"name": "Router A1", "type": "router"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Router A1"

    delete_response = client.delete(f"/api/devices/{device_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/devices/{device_id}")
    assert missing_response.status_code == 404


def test_device_validation_errors(client: TestClient) -> None:
    response = client.post("/api/devices", json={"name": "", "type": "router"})
    assert response.status_code == 422

    missing_response = client.get("/api/devices/999")
    assert missing_response.status_code == 404

