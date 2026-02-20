"""
Tests for settings endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from api.models.settings import SystemSettings


@pytest.mark.asyncio
async def test_list_settings(client: AsyncClient, admin_headers: dict, sample_settings: list):
    """Test listing all settings (admin only)."""
    response = await client.get("/api/settings", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, (list, dict))


@pytest.mark.asyncio
async def test_list_settings_non_admin(client: AsyncClient, auth_headers: dict):
    """Test non-admin cannot list settings."""
    response = await client.get("/api/settings", headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_settings_no_auth(client: AsyncClient):
    """Test unauthenticated cannot list settings."""
    response = await client.get("/api/settings")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_setting(client: AsyncClient, admin_headers: dict, sample_settings: list):
    """Test getting a specific setting."""
    setting = sample_settings[0]
    response = await client.get(f"/api/settings/{setting.key}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == setting.key


@pytest.mark.asyncio
async def test_get_setting_not_found(client: AsyncClient, admin_headers: dict):
    """Test getting nonexistent setting returns 404."""
    response = await client.get("/api/settings/nonexistent_setting", headers=admin_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_setting(client: AsyncClient, admin_headers: dict, sample_settings: list):
    """Test updating a setting."""
    setting = sample_settings[0]
    response = await client.put(
        f"/api/settings/{setting.key}",
        json={"value": "60"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["value"] == "60"


@pytest.mark.asyncio
async def test_update_setting_non_admin(
    client: AsyncClient, auth_headers: dict, sample_settings: list
):
    """Test non-admin cannot update settings."""
    setting = sample_settings[0]
    response = await client.put(
        f"/api/settings/{setting.key}",
        json={"value": "60"},
        headers=auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_bulk_update_settings(
    client: AsyncClient, admin_headers: dict, sample_settings: list
):
    """Test bulk updating settings."""
    updates = {sample_settings[0].key: "45", sample_settings[1].key: "120"}
    response = await client.put(
        "/api/settings",
        json=updates,
        headers=admin_headers,
    )
    assert response.status_code == 200
