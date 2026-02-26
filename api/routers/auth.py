"""
Authentication Router

Login, logout, and user management endpoints.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from api.auth.jwt import get_token_expiration_seconds
from api.database import get_db
from api.models.user import User
from api.schemas.auth import (
    LoginRequest,
    LoginResponse,
    PasswordChangeRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """
    Authenticate user and return access token.
    """
    # Find user
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.commit()

    # Create token
    access_token = create_access_token(
        subject=user.username,
        is_admin=user.is_admin,
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=get_token_expiration_seconds(),
        user=UserResponse.model_validate(user),
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Logout current user.

    Note: With JWT tokens, logout is typically handled client-side
    by discarding the token. This endpoint is provided for API
    completeness.
    """
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current authenticated user information.
    """
    return UserResponse.model_validate(current_user)


@router.put("/password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Change current user's password.
    """
    # Verify current password
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    current_user.password_hash = hash_password(request.new_password)
    await db.commit()

    return {"message": "Password changed successfully"}
