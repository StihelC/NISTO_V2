"""Connection API tests."""

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


def create_device(client: TestClient, name: str) -> int:
    response = client.post(
        "/api/devices",
        json={"name": name, "type": "router"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_connection_crud_happy_path(client: TestClient) -> None:
    device_a = create_device(client, "Device A")
    device_b = create_device(client, "Device B")

    response = client.post(
        "/api/connections",
        json={
            "source_device_id": device_a,
            "target_device_id": device_b,
            "link_type": "ethernet",
        },
    )
    assert response.status_code == 201
    connection_id = response.json()["id"]

    list_response = client.get("/api/connections")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = client.put(
        f"/api/connections/{connection_id}",
        json={"link_type": "fiber"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["link_type"] == "fiber"

    delete_response = client.delete(f"/api/connections/{connection_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/connections/{connection_id}")
    assert missing_response.status_code == 404


def test_connection_validation_errors(client: TestClient) -> None:
    device_a = create_device(client, "Device A")

    response = client.post(
        "/api/connections",
        json={
            "source_device_id": device_a,
            "target_device_id": device_a,
            "link_type": "ethernet",
        },
    )
    assert response.status_code == 400

    response = client.post(
        "/api/connections",
        json={
            "source_device_id": device_a,
            "target_device_id": 999,
            "link_type": "ethernet",
        },
    )
    assert response.status_code == 400

