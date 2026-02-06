"""
Multi-Day Configuration Router

Multi-day timelapse configuration management.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.database import get_db
from api.models.camera import Camera
from api.models.multiday_config import MultidayConfig
from api.models.user import User
from api.schemas.timelapse import (
    MultidayConfigCreate,
    MultidayConfigResponse,
    MultidayConfigUpdate,
)

router = APIRouter(prefix="/multiday", tags=["Multi-Day Timelapse"])


@router.get("", response_model=list[MultidayConfigResponse])
async def list_multiday_configs(
    camera_id: UUID = Query(None, description="Filter by camera"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MultidayConfigResponse]:
    """
    List all multi-day configurations.
    """
    query = select(MultidayConfig)

    if camera_id:
        query = query.where(MultidayConfig.camera_id == camera_id)

    query = query.order_by(MultidayConfig.name)

    result = await db.execute(query)
    configs = result.scalars().all()

    return [MultidayConfigResponse.model_validate(c) for c in configs]


@router.post("", response_model=MultidayConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_multiday_config(
    config_data: MultidayConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MultidayConfigResponse:
    """
    Create a new multi-day configuration.
    """
    # Verify camera exists
    result = await db.execute(
        select(Camera).where(Camera.id == config_data.camera_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found",
        )

    config = MultidayConfig(
        camera_id=config_data.camera_id,
        name=config_data.name,
        is_enabled=config_data.is_enabled,
        images_per_hour=config_data.images_per_hour,
        days_to_include=config_data.days_to_include,
        generation_day=config_data.generation_day,
        generation_time=config_data.generation_time,
        frame_rate=config_data.frame_rate,
        crf=config_data.crf,
        pixel_format=config_data.pixel_format,
    )

    db.add(config)
    await db.commit()
    await db.refresh(config)

    return MultidayConfigResponse.model_validate(config)


@router.get("/{config_id}", response_model=MultidayConfigResponse)
async def get_multiday_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MultidayConfigResponse:
    """
    Get a multi-day configuration by ID.
    """
    result = await db.execute(
        select(MultidayConfig).where(MultidayConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )

    return MultidayConfigResponse.model_validate(config)


@router.put("/{config_id}", response_model=MultidayConfigResponse)
async def update_multiday_config(
    config_id: UUID,
    config_data: MultidayConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MultidayConfigResponse:
    """
    Update a multi-day configuration.
    """
    result = await db.execute(
        select(MultidayConfig).where(MultidayConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )

    update_data = config_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)

    return MultidayConfigResponse.model_validate(config)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_multiday_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a multi-day configuration.
    """
    result = await db.execute(
        select(MultidayConfig).where(MultidayConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )

    await db.delete(config)
    await db.commit()


@router.post("/{config_id}/generate", response_model=dict)
async def trigger_multiday_generation(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Trigger multi-day timelapse generation.
    """
    result = await db.execute(
        select(MultidayConfig).where(MultidayConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )

    # TODO: Trigger async multi-day timelapse generation task

    return {"message": "Multi-day timelapse generation triggered", "config_id": str(config_id)}
