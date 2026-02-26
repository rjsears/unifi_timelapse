"""
Tests for authentication endpoints.
"""

import pytest
from httpx import AsyncClient

from api.models.user import User


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user: User):
    """Test successful login returns access token."""
    response = await client.post(
        "/api/auth/login",
        json={
            "username": "testuser@test.com",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, test_user: User):
    """Test login with wrong password fails."""
    response = await client.post(
        "/api/auth/login",
        json={
            "username": "testuser@test.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with nonexistent user fails."""
    response = await client.post(
        "/api/auth/login",
        json={
            "username": "nonexistent@test.com",
            "password": "anypassword",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, auth_headers: dict):
    """Test getting current user info."""
    response = await client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser@test.com"


@pytest.mark.asyncio
async def test_get_current_user_no_auth(client: AsyncClient):
    """Test getting current user without auth fails."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_updates_last_login(client: AsyncClient, db_session, test_user: User):
    """Test that successful login updates last_login_at timestamp."""
    from sqlalchemy import select
    from api.models.user import User as UserModel

    # Record initial state
    initial_last_login = test_user.last_login_at

    # Perform login
    response = await client.post(
        "/api/auth/login",
        json={
            "username": "testuser@test.com",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 200

    # Verify last_login_at was updated
    result = await db_session.execute(
        select(UserModel).where(UserModel.id == test_user.id)
    )
    updated_user = result.scalar_one()
    assert updated_user.last_login_at is not None
    if initial_last_login is not None:
        assert updated_user.last_login_at >= initial_last_login
