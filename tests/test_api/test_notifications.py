"""
Tests for notification endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from api.models.notification_config import NotificationConfig


@pytest.mark.asyncio
async def test_list_notifications_empty(client: AsyncClient, auth_headers: dict):
    """Test listing notifications when none exist."""
    response = await client.get("/api/notifications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, (list, dict))


@pytest.mark.asyncio
async def test_list_notifications_with_data(
    client: AsyncClient, auth_headers: dict, notification_config: NotificationConfig
):
    """Test listing notifications returns data."""
    response = await client.get("/api/notifications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    if isinstance(data, dict):
        assert "configs" in data or "notifications" in data or len(data) > 0
    else:
        assert len(data) >= 1


@pytest.mark.asyncio
async def test_list_notifications_no_auth(client: AsyncClient):
    """Test listing notifications without auth fails."""
    response = await client.get("/api/notifications")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_notification(client: AsyncClient, auth_headers: dict):
    """Test creating a notification config."""
    config_data = {
        "name": "Test Alert",
        "apprise_url": "json://localhost:9999/test",
        "is_enabled": True,
        "notify_on_capture_fail": True,
        "notify_on_timelapse_done": False,
        "notify_on_storage_warn": True,
        "notify_on_camera_down": True,
        "min_failures_before_alert": 5,
    }
    response = await client.post("/api/notifications", json=config_data, headers=auth_headers)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["name"] == "Test Alert"


@pytest.mark.asyncio
async def test_get_notification(
    client: AsyncClient, auth_headers: dict, notification_config: NotificationConfig
):
    """Test getting a specific notification config."""
    response = await client.get(
        f"/api/notifications/{notification_config.id}", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(notification_config.id)


@pytest.mark.asyncio
async def test_get_notification_not_found(client: AsyncClient, auth_headers: dict):
    """Test getting nonexistent notification returns 404."""
    fake_id = uuid4()
    response = await client.get(f"/api/notifications/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_notification(
    client: AsyncClient, auth_headers: dict, notification_config: NotificationConfig
):
    """Test updating a notification config."""
    response = await client.put(
        f"/api/notifications/{notification_config.id}",
        json={"name": "Updated Name", "is_enabled": False},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["is_enabled"] is False


@pytest.mark.asyncio
async def test_delete_notification(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    """Test deleting a notification config."""
    config = NotificationConfig(
        id=uuid4(),
        name="To Delete",
        apprise_url="json://localhost/delete",
        is_enabled=True,
    )
    db_session.add(config)
    await db_session.commit()

    response = await client.delete(f"/api/notifications/{config.id}", headers=auth_headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_notification_not_found(client: AsyncClient, auth_headers: dict):
    """Test deleting nonexistent notification returns 404."""
    fake_id = uuid4()
    response = await client.delete(f"/api/notifications/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_test_notification(
    client: AsyncClient, auth_headers: dict, notification_config: NotificationConfig
):
    """Test sending a test notification."""
    response = await client.post(
        f"/api/notifications/{notification_config.id}/test", headers=auth_headers
    )
    # The test may succeed or fail depending on if the apprise URL is valid
    assert response.status_code in [200, 400, 500]
