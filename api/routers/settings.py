"""
Settings Router

Global settings management.
"""


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_admin_user
from api.database import get_db
from api.models.settings import SystemSettings
from api.models.user import User
from api.schemas.settings import SettingResponse, SettingsListResponse, SettingUpdate

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=SettingsListResponse)
async def list_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> SettingsListResponse:
    """
    List all settings (admin only).
    """
    result = await db.execute(
        select(SystemSettings).order_by(SystemSettings.category, SystemSettings.key)
    )
    settings = result.scalars().all()

    # Get unique categories
    categories = list({s.category for s in settings})

    return SettingsListResponse(
        settings=[
            SettingResponse(
                id=s.id,
                key=s.key,
                value=s.get_typed_value(),
                type=s.type,
                category=s.category,
                description=s.description,
                updated_at=s.updated_at,
            )
            for s in settings
        ],
        categories=sorted(categories),
    )


@router.get("/{key}", response_model=SettingResponse)
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> SettingResponse:
    """
    Get a setting by key (admin only).
    """
    result = await db.execute(
        select(SystemSettings).where(SystemSettings.key == key)
    )
    setting = result.scalar_one_or_none()

    if setting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found",
        )

    return SettingResponse(
        id=setting.id,
        key=setting.key,
        value=setting.get_typed_value(),
        type=setting.type,
        category=setting.category,
        description=setting.description,
        updated_at=setting.updated_at,
    )


@router.put("/{key}", response_model=SettingResponse)
async def update_setting(
    key: str,
    update: SettingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> SettingResponse:
    """
    Update a setting (admin only).
    """
    result = await db.execute(
        select(SystemSettings).where(SystemSettings.key == key)
    )
    setting = result.scalar_one_or_none()

    if setting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found",
        )

    # Update value with type conversion
    setting.set_typed_value(update.value)

    await db.commit()
    await db.refresh(setting)

    return SettingResponse(
        id=setting.id,
        key=setting.key,
        value=setting.get_typed_value(),
        type=setting.type,
        category=setting.category,
        description=setting.description,
        updated_at=setting.updated_at,
    )
