"""
Multi-Day Configuration Router

Multi-day timelapse configuration management.
Supports two modes:
- Historical: Build timelapse from existing images
- Prospective: Collect images over time, then generate
"""

from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.database import get_db
from api.models.camera import Camera
from api.models.image import Image
from api.models.multiday_config import MultidayConfig
from api.models.timelapse import Timelapse
from api.models.user import User
from api.schemas.timelapse import (
    CancelCollectionRequest,
    CollectionProgressResponse,
    HistoricalGenerateRequest,
    HistoricalGenerateResponse,
    MultidayConfigCreate,
    MultidayConfigResponse,
    MultidayConfigUpdate,
    StartCollectionRequest,
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
    result = await db.execute(select(Camera).where(Camera.id == config_data.camera_id))
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
        mode=config_data.mode,
        auto_generate=config_data.auto_generate,
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
    result = await db.execute(select(MultidayConfig).where(MultidayConfig.id == config_id))
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
    result = await db.execute(select(MultidayConfig).where(MultidayConfig.id == config_id))
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
    result = await db.execute(select(MultidayConfig).where(MultidayConfig.id == config_id))
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
    result = await db.execute(select(MultidayConfig).where(MultidayConfig.id == config_id))
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )

    # TODO: Trigger async multi-day timelapse generation task

    return {"message": "Multi-day timelapse generation triggered", "config_id": str(config_id)}


# ============ Historical Mode Endpoints ============


@router.post("/generate-historical", response_model=HistoricalGenerateResponse)
async def generate_historical_timelapse(
    request: HistoricalGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HistoricalGenerateResponse:
    """
    Generate a one-off historical timelapse from existing images.
    This is a "Custom Timelapse" - it runs immediately without scheduling.
    """
    # Verify camera exists
    result = await db.execute(select(Camera).where(Camera.id == request.camera_id))
    camera = result.scalar_one_or_none()
    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found",
        )

    # Validate date range
    if request.end_date < request.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date",
        )

    # Check if there are images in the date range
    image_count = await db.execute(
        select(func.count())
        .select_from(Image)
        .where(
            Image.camera_id == request.camera_id,
            func.date(Image.captured_at) >= request.start_date,
            func.date(Image.captured_at) <= request.end_date,
        )
    )
    total_images = image_count.scalar() or 0

    if total_images == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No images found in the specified date range",
        )

    # Calculate expected frames based on images_per_hour
    days = (request.end_date - request.start_date).days + 1
    estimated_frames = request.images_per_hour * 24 * days

    # Create a timelapse record (will be processed by worker)
    timelapse = Timelapse(
        camera_id=request.camera_id,
        type="multiday",
        date_start=request.start_date,
        date_end=request.end_date,
        frame_rate=request.frame_rate,
        crf=request.crf,
        pixel_format=request.pixel_format,
        status="pending",
    )
    db.add(timelapse)
    await db.commit()
    await db.refresh(timelapse)

    # TODO: Trigger worker task to generate timelapse with images_per_hour parameter

    return HistoricalGenerateResponse(
        timelapse_id=timelapse.id,
        message=f"Historical timelapse generation started for {days} days",
        estimated_frames=estimated_frames,
    )


# ============ Prospective Mode Endpoints ============


@router.post("/{config_id}/start-collection", response_model=CollectionProgressResponse)
async def start_prospective_collection(
    config_id: UUID,
    request: StartCollectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CollectionProgressResponse:
    """
    Start prospective image collection for a config.
    Images captured during the collection period will be protected.
    """
    result = await db.execute(select(MultidayConfig).where(MultidayConfig.id == config_id))
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )

    if config.status == "collecting":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Collection is already in progress",
        )

    # Set up prospective collection
    today = date.today()
    config.mode = "prospective"
    config.status = "collecting"
    config.collection_start_date = today
    config.collection_end_date = today + timedelta(days=request.days_to_collect - 1)
    config.collection_progress_days = 0
    config.days_to_include = request.days_to_collect

    await db.commit()
    await db.refresh(config)

    # Get current protected images count (should be 0 at start)
    protected_count = await db.execute(
        select(func.count()).select_from(Image).where(Image.protected_by_config_id == config_id)
    )
    protected_images = protected_count.scalar() or 0

    return CollectionProgressResponse(
        config_id=config.id,
        status=config.status,
        mode=config.mode,
        days_to_collect=config.days_to_include,
        days_collected=config.collection_progress_days,
        progress_percent=config.collection_progress_percent,
        collection_start_date=config.collection_start_date,
        collection_end_date=config.collection_end_date,
        protected_images_count=protected_images,
        auto_generate=config.auto_generate,
    )


@router.get("/{config_id}/progress", response_model=CollectionProgressResponse)
async def get_collection_progress(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CollectionProgressResponse:
    """
    Get progress of a prospective collection.
    """
    result = await db.execute(select(MultidayConfig).where(MultidayConfig.id == config_id))
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )

    # Get protected images count
    protected_count = await db.execute(
        select(func.count()).select_from(Image).where(Image.protected_by_config_id == config_id)
    )
    protected_images = protected_count.scalar() or 0

    return CollectionProgressResponse(
        config_id=config.id,
        status=config.status,
        mode=config.mode,
        days_to_collect=config.days_to_include,
        days_collected=config.collection_progress_days,
        progress_percent=config.collection_progress_percent,
        collection_start_date=config.collection_start_date,
        collection_end_date=config.collection_end_date,
        protected_images_count=protected_images,
        auto_generate=config.auto_generate,
    )


@router.post("/{config_id}/cancel-collection", response_model=dict)
async def cancel_prospective_collection(
    config_id: UUID,
    request: CancelCollectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Cancel a prospective collection.
    Optionally unprotect the collected images.
    """
    result = await db.execute(select(MultidayConfig).where(MultidayConfig.id == config_id))
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )

    if config.status != "collecting":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active collection to cancel",
        )

    # Get count of protected images before unprotecting
    protected_count = await db.execute(
        select(func.count()).select_from(Image).where(Image.protected_by_config_id == config_id)
    )
    protected_images = protected_count.scalar() or 0

    # Optionally unprotect images
    if request.unprotect_images:
        await db.execute(
            Image.__table__.update()
            .where(Image.protected_by_config_id == config_id)
            .values(
                is_protected=False,
                protection_reason=None,
                protected_by_config_id=None,
            )
        )

    # Reset config status
    config.status = "idle"
    config.collection_start_date = None
    config.collection_end_date = None
    config.collection_progress_days = 0

    await db.commit()

    return {
        "message": "Collection cancelled",
        "images_unprotected": protected_images if request.unprotect_images else 0,
    }
