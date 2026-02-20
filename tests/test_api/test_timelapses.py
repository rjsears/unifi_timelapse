"""
Tests for timelapse endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from datetime import date, timedelta

from api.models.camera import Camera
from api.models.timelapse import Timelapse


@pytest.mark.asyncio
async def test_list_timelapses_empty(client: AsyncClient, auth_headers: dict):
    """Test listing timelapses when none exist."""
    response = await client.get("/api/timelapses", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "timelapses" in data
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_timelapses_with_data(
    client: AsyncClient, auth_headers: dict, sample_timelapse: Timelapse
):
    """Test listing timelapses returns data."""
    response = await client.get("/api/timelapses", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_timelapses_filter_by_camera(
    client: AsyncClient, auth_headers: dict, sample_camera: Camera, sample_timelapse: Timelapse
):
    """Test filtering timelapses by camera."""
    response = await client.get(
        f"/api/timelapses?camera_id={sample_camera.id}", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_timelapses_filter_by_status(
    client: AsyncClient, auth_headers: dict, sample_timelapse: Timelapse
):
    """Test filtering timelapses by status."""
    response = await client.get("/api/timelapses?status=completed", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    for tl in data["timelapses"]:
        assert tl["status"] == "completed"


@pytest.mark.asyncio
async def test_list_timelapses_pagination(
    client: AsyncClient, auth_headers: dict, sample_timelapse: Timelapse
):
    """Test timelapse pagination."""
    response = await client.get("/api/timelapses?page=1&per_page=5", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["timelapses"]) <= 5


@pytest.mark.asyncio
async def test_list_timelapses_no_auth(client: AsyncClient):
    """Test listing timelapses without auth fails."""
    response = await client.get("/api/timelapses")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_timelapse(client: AsyncClient, auth_headers: dict, sample_timelapse: Timelapse):
    """Test getting a specific timelapse."""
    response = await client.get(f"/api/timelapses/{sample_timelapse.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_timelapse.id)


@pytest.mark.asyncio
async def test_get_timelapse_not_found(client: AsyncClient, auth_headers: dict):
    """Test getting nonexistent timelapse returns 404."""
    fake_id = uuid4()
    response = await client.get(f"/api/timelapses/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_timelapse_stats(
    client: AsyncClient, auth_headers: dict, sample_timelapse: Timelapse
):
    """Test timelapse statistics endpoint."""
    response = await client.get("/api/timelapses/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_delete_timelapse(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, sample_camera: Camera
):
    """Test deleting a timelapse."""
    timelapse = Timelapse(
        id=uuid4(),
        camera_id=sample_camera.id,
        type="daily",
        date_start=date.today() - timedelta(days=2),
        date_end=date.today() - timedelta(days=2),
        status="completed",
    )
    db_session.add(timelapse)
    await db_session.commit()

    response = await client.delete(f"/api/timelapses/{timelapse.id}", headers=auth_headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_timelapse_not_found(client: AsyncClient, auth_headers: dict):
    """Test deleting nonexistent timelapse returns 404."""
    fake_id = uuid4()
    response = await client.delete(f"/api/timelapses/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_camera_timelapses(
    client: AsyncClient, auth_headers: dict, sample_camera: Camera, sample_timelapse: Timelapse
):
    """Test listing timelapses for a specific camera."""
    response = await client.get(f"/api/timelapses/camera/{sample_camera.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "timelapses" in data
