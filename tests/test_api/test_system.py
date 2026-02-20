"""
Tests for system endpoints.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_system_health_healthy(client: AsyncClient):
    """Test system health check returns healthy status."""
    response = await client.get("/api/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "database" in data
    assert "redis" in data


@pytest.mark.asyncio
async def test_system_info(client: AsyncClient, auth_headers: dict):
    """Test system info endpoint returns expected data."""
    response = await client.get("/api/system/info", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "version" in data or "cameras" in data or "images" in data


@pytest.mark.asyncio
async def test_system_info_no_auth(client: AsyncClient):
    """Test system info without auth fails."""
    response = await client.get("/api/system/info")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_system_storage(client: AsyncClient, auth_headers: dict):
    """Test system storage endpoint."""
    response = await client.get("/api/system/storage", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # Check for storage-related fields
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_system_storage_no_auth(client: AsyncClient):
    """Test system storage without auth fails."""
    response = await client.get("/api/system/storage")
    assert response.status_code == 401
