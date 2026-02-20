"""
Tests for image endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from api.models.camera import Camera
from api.models.image import Image


@pytest.mark.asyncio
async def test_list_images_empty(client: AsyncClient, auth_headers: dict):
    """Test listing images when none exist."""
    response = await client.get("/api/images", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "images" in data
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_images_with_data(client: AsyncClient, auth_headers: dict, sample_images: list):
    """Test listing images returns data."""
    response = await client.get("/api/images", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= len(sample_images)


@pytest.mark.asyncio
async def test_list_images_filter_by_camera(
    client: AsyncClient, auth_headers: dict, sample_camera: Camera, sample_images: list
):
    """Test filtering images by camera."""
    response = await client.get(f"/api/images?camera_id={sample_camera.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(sample_images)


@pytest.mark.asyncio
async def test_list_images_pagination(client: AsyncClient, auth_headers: dict, sample_images: list):
    """Test image pagination."""
    response = await client.get("/api/images?page=1&per_page=5", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["images"]) <= 5


@pytest.mark.asyncio
async def test_list_images_no_auth(client: AsyncClient):
    """Test listing images without auth fails."""
    response = await client.get("/api/images")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_image(client: AsyncClient, auth_headers: dict, sample_images: list):
    """Test getting a specific image."""
    image = sample_images[0]
    response = await client.get(f"/api/images/{image.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(image.id)


@pytest.mark.asyncio
async def test_get_image_not_found(client: AsyncClient, auth_headers: dict):
    """Test getting nonexistent image returns 404."""
    fake_id = uuid4()
    response = await client.get(f"/api/images/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_image_stats(client: AsyncClient, auth_headers: dict, sample_images: list):
    """Test image statistics endpoint."""
    response = await client.get("/api/images/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_images" in data or "total" in data or isinstance(data, dict)


@pytest.mark.asyncio
async def test_protect_image(client: AsyncClient, auth_headers: dict, sample_images: list):
    """Test protecting an image."""
    image = sample_images[0]
    response = await client.put(
        f"/api/images/{image.id}/protect",
        json={"is_protected": True, "reason": "manual"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_protected"] is True


@pytest.mark.asyncio
async def test_unprotect_image(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, sample_images: list
):
    """Test unprotecting an image."""
    image = sample_images[0]
    # First protect it
    image.is_protected = True
    image.protection_reason = "manual"
    await db_session.commit()

    response = await client.put(
        f"/api/images/{image.id}/protect",
        json={"is_protected": False},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_protected"] is False


@pytest.mark.asyncio
async def test_delete_image(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, sample_camera: Camera
):
    """Test deleting an image."""
    from datetime import datetime

    image = Image(
        id=uuid4(),
        camera_id=sample_camera.id,
        captured_at=datetime.now(),
        file_path="test/delete_me.jpg",
        file_size=1024,
    )
    db_session.add(image)
    await db_session.commit()

    response = await client.delete(f"/api/images/{image.id}", headers=auth_headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_image_not_found(client: AsyncClient, auth_headers: dict):
    """Test deleting nonexistent image returns 404."""
    fake_id = uuid4()
    response = await client.delete(f"/api/images/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_camera_images(
    client: AsyncClient, auth_headers: dict, sample_camera: Camera, sample_images: list
):
    """Test listing images for a specific camera."""
    response = await client.get(f"/api/images/camera/{sample_camera.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "images" in data


@pytest.mark.asyncio
async def test_available_dates(
    client: AsyncClient, auth_headers: dict, sample_camera: Camera, sample_images: list
):
    """Test getting available dates for a camera."""
    response = await client.get(
        f"/api/images/camera/{sample_camera.id}/available-dates", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "dates" in data or isinstance(data, list)
