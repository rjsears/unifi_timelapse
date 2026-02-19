"""
Notifications Router

Notification configuration management.
"""

from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.config import get_settings
from api.database import get_db
from api.models.notification_config import NotificationConfig
from api.models.user import User
from api.schemas.settings import (
    NotificationConfigCreate,
    NotificationConfigResponse,
    NotificationConfigUpdate,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationConfigResponse])
async def list_notification_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NotificationConfigResponse]:
    """
    List all notification configurations.
    """
    result = await db.execute(select(NotificationConfig).order_by(NotificationConfig.name))
    configs = result.scalars().all()

    return [NotificationConfigResponse.model_validate(c) for c in configs]


@router.post("", response_model=NotificationConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_notification_config(
    config_data: NotificationConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationConfigResponse:
    """
    Create a new notification configuration.
    """
    config = NotificationConfig(
        name=config_data.name,
        apprise_url=config_data.apprise_url,
        is_enabled=config_data.is_enabled,
        notify_on_capture_fail=config_data.notify_on_capture_fail,
        notify_on_timelapse_done=config_data.notify_on_timelapse_done,
        notify_on_storage_warn=config_data.notify_on_storage_warn,
        notify_on_camera_down=config_data.notify_on_camera_down,
        min_failures_before_alert=config_data.min_failures_before_alert,
    )

    db.add(config)
    await db.commit()
    await db.refresh(config)

    return NotificationConfigResponse.model_validate(config)


@router.get("/{config_id}", response_model=NotificationConfigResponse)
async def get_notification_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationConfigResponse:
    """
    Get a notification configuration by ID.
    """
    result = await db.execute(select(NotificationConfig).where(NotificationConfig.id == config_id))
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification configuration not found",
        )

    return NotificationConfigResponse.model_validate(config)


@router.put("/{config_id}", response_model=NotificationConfigResponse)
async def update_notification_config(
    config_id: UUID,
    config_data: NotificationConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationConfigResponse:
    """
    Update a notification configuration.
    """
    result = await db.execute(select(NotificationConfig).where(NotificationConfig.id == config_id))
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification configuration not found",
        )

    update_data = config_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)

    return NotificationConfigResponse.model_validate(config)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a notification configuration.
    """
    result = await db.execute(select(NotificationConfig).where(NotificationConfig.id == config_id))
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification configuration not found",
        )

    await db.delete(config)
    await db.commit()


@router.post("/{config_id}/test")
async def test_notification(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Send a test notification.
    """
    result = await db.execute(select(NotificationConfig).where(NotificationConfig.id == config_id))
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification configuration not found",
        )

    settings = get_settings()

    # Send test notification via Apprise
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.apprise_url}/notify",
                json={
                    "urls": config.apprise_url,
                    "title": "UniFi Timelapse Test",
                    "body": "This is a test notification from the UniFi Timelapse system.",
                    "type": "info",
                },
                timeout=30,
            )
            response.raise_for_status()

            return {"success": True, "message": "Test notification sent"}

    except httpx.HTTPError as e:
        return {"success": False, "error": str(e)}
