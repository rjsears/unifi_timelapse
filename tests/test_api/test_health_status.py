"""
Tests for health status endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from api.models.camera import Camera
from api.models.camera_health import CameraHealth


@pytest.mark.asyncio
async def test_get_all_cameras_health(
    client: AsyncClient, auth_headers: dict, sample_camera: Camera, camera_health_records: list
):
    """Test getting health status for all cameras."""
    response = await client.get("/api/health/cameras", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_all_cameras_health_empty(client: AsyncClient, auth_headers: dict):
    """Test getting health when no cameras exist."""
    response = await client.get("/api/health/cameras", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_all_cameras_health_no_auth(client: AsyncClient):
    """Test getting health without auth fails."""
    response = await client.get("/api/health/cameras")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_camera_health(
    client: AsyncClient, auth_headers: dict, sample_camera: Camera, camera_health_records: list
):
    """Test getting health status for a specific camera."""
    response = await client.get(f"/api/health/cameras/{sample_camera.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["camera_id"] == str(sample_camera.id)
    assert data["camera_name"] == sample_camera.name


@pytest.mark.asyncio
async def test_get_camera_health_not_found(client: AsyncClient, auth_headers: dict):
    """Test getting health for nonexistent camera."""
    fake_id = uuid4()
    response = await client.get(f"/api/health/cameras/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_camera_health_history(
    client: AsyncClient, auth_headers: dict, sample_camera: Camera, camera_health_records: list
):
    """Test getting health history for a camera."""
    response = await client.get(
        f"/api/health/cameras/{sample_camera.id}/history", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "camera_id" in data
    assert "checks" in data
    assert "uptime_percent" in data


@pytest.mark.asyncio
async def test_get_camera_health_history_with_hours(
    client: AsyncClient, auth_headers: dict, sample_camera: Camera, camera_health_records: list
):
    """Test getting health history with custom hours parameter."""
    response = await client.get(
        f"/api/health/cameras/{sample_camera.id}/history?hours=12",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "uptime_percent" in data


@pytest.mark.asyncio
async def test_get_camera_health_history_not_found(client: AsyncClient, auth_headers: dict):
    """Test getting history for nonexistent camera."""
    fake_id = uuid4()
    response = await client.get(f"/api/health/cameras/{fake_id}/history", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_health_summary(client: AsyncClient, auth_headers: dict, sample_camera: Camera):
    """Test getting overall health summary."""
    response = await client.get("/api/health/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_cameras" in data
    assert "cameras_healthy" in data
    assert "cameras_with_issues" in data


@pytest.mark.asyncio
async def test_get_health_summary_no_auth(client: AsyncClient):
    """Test getting health summary without auth fails."""
    response = await client.get("/api/health/summary")
    assert response.status_code == 401
