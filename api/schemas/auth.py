"""
Authentication Schemas

Pydantic schemas for authentication endpoints.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Schema for login request."""

    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Schema for login response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class UserResponse(BaseModel):
    """Schema for user response."""

    id: UUID
    username: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    model_config = {"from_attributes": True}


class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""

    sub: str
    exp: datetime
    iat: datetime
    is_admin: bool = False
