"""
Tests for API health endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test the health check endpoint returns OK."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_redirect(client: AsyncClient):
    """Test root redirects to docs or returns info."""
    response = await client.get("/", follow_redirects=False)
    # Should either redirect or return API info
    assert response.status_code in [200, 307, 308]
