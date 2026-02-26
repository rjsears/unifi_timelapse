"""
Tests for authentication endpoints.
"""

import pytest
from datetime import datetime
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

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


@pytest.mark.asyncio
async def test_login_function_directly():
    """Test login function directly to ensure datetime.utcnow() is called."""
    from api.routers.auth import login
    from api.schemas.auth import LoginRequest

    # Create mock user
    mock_user = MagicMock()
    mock_user.username = "test@test.com"
    mock_user.password_hash = "$2b$12$test"  # placeholder
    mock_user.is_active = True
    mock_user.is_admin = False
    mock_user.last_login_at = None

    # Create mock db
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute.return_value = mock_result
    mock_db.commit = AsyncMock()

    # Create login request
    request = LoginRequest(username="test@test.com", password="testpassword")

    # Mock verify_password to return True
    with patch("api.routers.auth.verify_password", return_value=True):
        with patch("api.routers.auth.create_access_token", return_value="mock_token"):
            with patch("api.routers.auth.get_token_expiration_seconds", return_value=3600):
                response = await login(request, mock_db)

    # Verify last_login_at was set
    assert mock_user.last_login_at is not None
    assert isinstance(mock_user.last_login_at, datetime)
    mock_db.commit.assert_called_once()
