"""
Images Router

Image management endpoints.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.database import get_db
from api.models.camera import Camera
from api.models.image import Image
from api.models.user import User
from api.schemas.image import (
    ImageListResponse,
    ImageProtectRequest,
    ImageResponse,
)

router = APIRouter(prefix="/images", tags=["Images"])


@router.get("", response_model=ImageListResponse)
async def list_images(
    camera_id: Optional[UUID] = Query(None, description="Filter by camera"),
    date_filter: Optional[date] = Query(None, description="Filter by date"),
    protected_only: bool = Query(False, description="Only protected images"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ImageListResponse:
    """
    List images with optional filters.
    """
    query = select(Image)

    if camera_id:
        query = query.where(Image.camera_id == camera_id)

    if date_filter:
        query = query.where(func.date(Image.captured_at) == date_filter)

    if protected_only:
        query = query.where(Image.is_protected == True)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Add pagination and ordering
    query = query.order_by(Image.captured_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    images = result.scalars().all()

    return ImageListResponse(
        images=[ImageResponse.model_validate(img) for img in images],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/stats")
async def get_image_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get image statistics.
    """
    # Get today's date range in UTC
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Count images captured today
    today_count = await db.execute(
        select(func.count()).select_from(Image).where(
            Image.captured_at >= today_start
        )
    )
    today = today_count.scalar() or 0

    # Count total images
    total_count = await db.execute(
        select(func.count()).select_from(Image)
    )
    total = total_count.scalar() or 0

    return {
        "today": today,
        "total": total,
    }


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ImageResponse:
    """
    Get an image by ID.
    """
    result = await db.execute(
        select(Image).where(Image.id == image_id)
    )
    image = result.scalar_one_or_none()

    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    return ImageResponse.model_validate(image)


@router.put("/{image_id}/protect", response_model=ImageResponse)
async def protect_image(
    image_id: UUID,
    request: ImageProtectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ImageResponse:
    """
    Protect or unprotect an image from cleanup.
    """
    result = await db.execute(
        select(Image).where(Image.id == image_id)
    )
    image = result.scalar_one_or_none()

    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    image.is_protected = request.is_protected
    image.protection_reason = request.reason if request.is_protected else None

    await db.commit()
    await db.refresh(image)

    return ImageResponse.model_validate(image)


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete an image.
    """
    result = await db.execute(
        select(Image).where(Image.id == image_id)
    )
    image = result.scalar_one_or_none()

    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    # Delete file from disk
    import os
    from api.config import get_settings
    settings = get_settings()
    file_path = f"{settings.output_base_path}/{image.file_path}"
    if os.path.exists(file_path):
        os.remove(file_path)

    await db.delete(image)
    await db.commit()


@router.get("/camera/{camera_id}", response_model=ImageListResponse)
async def list_camera_images(
    camera_id: UUID,
    date_filter: Optional[date] = Query(None, description="Filter by date"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ImageListResponse:
    """
    List images for a specific camera.
    """
    # Verify camera exists
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found",
        )

    return await list_images(
        camera_id=camera_id,
        date_filter=date_filter,
        protected_only=False,
        page=page,
        per_page=per_page,
        db=db,
        current_user=current_user,
    )


@router.get("/camera/{camera_id}/latest", response_model=ImageResponse)
async def get_latest_image(
    camera_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ImageResponse:
    """
    Get the latest image for a camera.
    """
    result = await db.execute(
        select(Image)
        .where(Image.camera_id == camera_id)
        .order_by(Image.captured_at.desc())
        .limit(1)
    )
    image = result.scalar_one_or_none()

    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No images found for this camera",
        )

    return ImageResponse.model_validate(image)
