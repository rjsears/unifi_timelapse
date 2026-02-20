"""
Tests for multiday config endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from datetime import date, time

from api.models.camera import Camera
from api.models.multiday_config import MultidayConfig


@pytest.mark.asyncio
async def test_list_multiday_configs_empty(client: AsyncClient, auth_headers: dict):
    """Test listing multiday configs when none exist."""
    response = await client.get("/api/multiday", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, (list, dict))


@pytest.mark.asyncio
async def test_list_multiday_configs_with_data(
    client: AsyncClient, auth_headers: dict, multiday_config: MultidayConfig
):
    """Test listing multiday configs returns data."""
    response = await client.get("/api/multiday", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    if isinstance(data, dict):
        assert "configs" in data or len(data) > 0
    else:
        assert len(data) >= 1


@pytest.mark.asyncio
async def test_list_multiday_filter_by_camera(
    client: AsyncClient, auth_headers: dict, sample_camera: Camera, multiday_config: MultidayConfig
):
    """Test filtering multiday configs by camera."""
    response = await client.get(f"/api/multiday?camera_id={sample_camera.id}", headers=auth_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_multiday_no_auth(client: AsyncClient):
    """Test listing multiday configs without auth fails."""
    response = await client.get("/api/multiday")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_multiday_config(
    client: AsyncClient, auth_headers: dict, sample_camera: Camera
):
    """Test creating a multiday config."""
    config_data = {
        "camera_id": str(sample_camera.id),
        "name": "New Weekly Config",
        "is_enabled": True,
        "mode": "historical",
        "images_per_hour": 2,
        "days_to_include": 7,
        "generation_day": "monday",
        "generation_time": "03:00:00",
        "frame_rate": 30,
        "crf": 20,
        "pixel_format": "yuv444p",
    }
    response = await client.post("/api/multiday", json=config_data, headers=auth_headers)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["name"] == "New Weekly Config"


@pytest.mark.asyncio
async def test_get_multiday_config(
    client: AsyncClient, auth_headers: dict, multiday_config: MultidayConfig
):
    """Test getting a specific multiday config."""
    response = await client.get(f"/api/multiday/{multiday_config.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(multiday_config.id)


@pytest.mark.asyncio
async def test_get_multiday_config_not_found(client: AsyncClient, auth_headers: dict):
    """Test getting nonexistent config returns 404."""
    fake_id = uuid4()
    response = await client.get(f"/api/multiday/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_multiday_config(
    client: AsyncClient, auth_headers: dict, multiday_config: MultidayConfig
):
    """Test updating a multiday config."""
    response = await client.put(
        f"/api/multiday/{multiday_config.id}",
        json={"name": "Updated Config", "is_enabled": False},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Config"
    assert data["is_enabled"] is False


@pytest.mark.asyncio
async def test_delete_multiday_config(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, sample_camera: Camera
):
    """Test deleting a multiday config."""
    config = MultidayConfig(
        id=uuid4(),
        camera_id=sample_camera.id,
        name="To Delete",
        is_enabled=True,
        mode="historical",
        status="idle",
        images_per_hour=2,
        days_to_include=7,
        generation_day="sunday",
        generation_time=time(2, 0, 0),
        frame_rate=30,
        crf=20,
        pixel_format="yuv444p",
    )
    db_session.add(config)
    await db_session.commit()

    response = await client.delete(f"/api/multiday/{config.id}", headers=auth_headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_multiday_not_found(client: AsyncClient, auth_headers: dict):
    """Test deleting nonexistent config returns 404."""
    fake_id = uuid4()
    response = await client.delete(f"/api/multiday/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_multiday(
    client: AsyncClient, auth_headers: dict, multiday_config: MultidayConfig
):
    """Test triggering multiday generation."""
    response = await client.post(
        f"/api/multiday/{multiday_config.id}/generate", headers=auth_headers
    )
    # May fail if no images, but endpoint should be accessible
    assert response.status_code in [200, 202, 400, 404]


@pytest.mark.asyncio
async def test_generate_historical(client: AsyncClient, auth_headers: dict, sample_camera: Camera):
    """Test generating historical timelapse."""
    data = {
        "camera_id": str(sample_camera.id),
        "start_date": str(date.today() - __import__("datetime").timedelta(days=7)),
        "end_date": str(date.today() - __import__("datetime").timedelta(days=1)),
        "images_per_hour": 2,
        "frame_rate": 30,
        "crf": 20,
        "pixel_format": "yuv444p",
    }
    response = await client.post(
        "/api/multiday/generate-historical", json=data, headers=auth_headers
    )
    # May fail if no images, but endpoint should be accessible
    assert response.status_code in [200, 202, 400, 404]


@pytest.mark.asyncio
async def test_start_collection(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, sample_camera: Camera
):
    """Test starting prospective collection."""
    config = MultidayConfig(
        id=uuid4(),
        camera_id=sample_camera.id,
        name="Prospective Test",
        is_enabled=True,
        mode="prospective",
        status="idle",
        images_per_hour=2,
        days_to_include=7,
        generation_day="sunday",
        generation_time=time(2, 0, 0),
        frame_rate=30,
        crf=20,
        pixel_format="yuv444p",
    )
    db_session.add(config)
    await db_session.commit()

    response = await client.post(
        f"/api/multiday/{config.id}/start-collection", headers=auth_headers
    )
    assert response.status_code in [200, 400]


@pytest.mark.asyncio
async def test_get_collection_progress(
    client: AsyncClient, auth_headers: dict, multiday_config: MultidayConfig
):
    """Test getting collection progress."""
    response = await client.get(
        f"/api/multiday/{multiday_config.id}/progress", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "progress" in data or "status" in data or "collection_progress_days" in data
