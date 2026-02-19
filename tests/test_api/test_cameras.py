"""
Tests for camera endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.camera import Camera


@pytest.mark.asyncio
async def test_list_cameras_empty(client: AsyncClient, auth_headers: dict):
    """Test listing cameras when none exist."""
    response = await client.get("/api/cameras", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["cameras"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_camera(client: AsyncClient, auth_headers: dict):
    """Test creating a camera."""
    camera_data = {
        "name": "Test Camera",
        "ip_address": "192.168.1.100",
        "is_active": True,
        "capture_interval": 60,
    }
    response = await client.post(
        "/api/cameras",
        json=camera_data,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Camera"
    assert data["ip_address"] == "192.168.1.100"
    assert data["is_active"] is True
    assert data["capture_interval"] == 60
    assert "id" in data
    assert data["url"] == "http://192.168.1.100/snap.jpeg"


@pytest.mark.asyncio
async def test_create_camera_no_auth(client: AsyncClient):
    """Test creating a camera without auth fails."""
    camera_data = {
        "name": "Test Camera",
        "ip_address": "192.168.1.100",
    }
    response = await client.post("/api/cameras", json=camera_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_camera_missing_host(client: AsyncClient, auth_headers: dict):
    """Test creating a camera without hostname or IP fails."""
    camera_data = {
        "name": "Test Camera",
        "is_active": True,
    }
    response = await client.post(
        "/api/cameras",
        json=camera_data,
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_camera(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    """Test getting a specific camera."""
    from uuid import uuid4

    camera = Camera(
        id=uuid4(),
        name="Test Camera",
        ip_address="192.168.1.100",
        is_active=True,
        capture_interval=60,
    )
    db_session.add(camera)
    await db_session.commit()
    await db_session.refresh(camera)

    response = await client.get(
        f"/api/cameras/{camera.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Camera"


@pytest.mark.asyncio
async def test_get_camera_not_found(client: AsyncClient, auth_headers: dict):
    """Test getting a nonexistent camera."""
    from uuid import uuid4

    fake_id = uuid4()
    response = await client.get(
        f"/api/cameras/{fake_id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_camera(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    """Test updating a camera."""
    from uuid import uuid4

    camera = Camera(
        id=uuid4(),
        name="Original Name",
        ip_address="192.168.1.100",
        is_active=True,
        capture_interval=60,
    )
    db_session.add(camera)
    await db_session.commit()
    await db_session.refresh(camera)

    response = await client.put(
        f"/api/cameras/{camera.id}",
        json={"name": "Updated Name"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_camera(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    """Test deleting a camera."""
    from uuid import uuid4

    camera = Camera(
        id=uuid4(),
        name="To Delete",
        ip_address="192.168.1.100",
        is_active=True,
        capture_interval=60,
    )
    db_session.add(camera)
    await db_session.commit()
    await db_session.refresh(camera)

    response = await client.delete(
        f"/api/cameras/{camera.id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get(
        f"/api/cameras/{camera.id}",
        headers=auth_headers,
    )
    assert response.status_code == 404
