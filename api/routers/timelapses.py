"""
Timelapses Router

Timelapse management endpoints.
"""

import os
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.config import get_settings
from api.database import get_db
from api.models.camera import Camera
from api.models.timelapse import Timelapse
from api.models.user import User
from api.schemas.timelapse import (
    TimelapseCreateRequest,
    TimelapseListResponse,
    TimelapseResponse,
)

router = APIRouter(prefix="/timelapses", tags=["Timelapses"])


@router.get("", response_model=TimelapseListResponse)
async def list_timelapses(
    camera_id: Optional[UUID] = Query(None, description="Filter by camera"),
    timelapse_type: Optional[str] = Query(None, description="Filter by type (daily/multiday)"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TimelapseListResponse:
    """
    List timelapses with optional filters.
    """
    query = select(Timelapse)

    if camera_id:
        query = query.where(Timelapse.camera_id == camera_id)

    if timelapse_type:
        query = query.where(Timelapse.type == timelapse_type)

    if status_filter:
        query = query.where(Timelapse.status == status_filter)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Add pagination and ordering
    query = query.order_by(Timelapse.date_start.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    timelapses = result.scalars().all()

    return TimelapseListResponse(
        timelapses=[TimelapseResponse.model_validate(tl) for tl in timelapses],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/stats")
async def get_timelapse_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get timelapse statistics.
    """
    # Count completed timelapses
    completed_count = await db.execute(
        select(func.count()).select_from(Timelapse).where(Timelapse.status == "completed")
    )
    completed = completed_count.scalar() or 0

    # Count pending timelapses
    pending_count = await db.execute(
        select(func.count())
        .select_from(Timelapse)
        .where(Timelapse.status.in_(["pending", "processing"]))
    )
    pending = pending_count.scalar() or 0

    # Count failed timelapses
    failed_count = await db.execute(
        select(func.count()).select_from(Timelapse).where(Timelapse.status == "failed")
    )
    failed = failed_count.scalar() or 0

    return {
        "completed": completed,
        "pending": pending,
        "failed": failed,
    }


@router.get("/{timelapse_id}", response_model=TimelapseResponse)
async def get_timelapse(
    timelapse_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TimelapseResponse:
    """
    Get a timelapse by ID.
    """
    result = await db.execute(select(Timelapse).where(Timelapse.id == timelapse_id))
    timelapse = result.scalar_one_or_none()

    if timelapse is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timelapse not found",
        )

    return TimelapseResponse.model_validate(timelapse)


@router.get("/{timelapse_id}/video")
async def get_timelapse_video(
    timelapse_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """
    Stream timelapse video file.
    """
    result = await db.execute(select(Timelapse).where(Timelapse.id == timelapse_id))
    timelapse = result.scalar_one_or_none()

    if timelapse is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timelapse not found",
        )

    if not timelapse.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timelapse video file not available",
        )

    settings = get_settings()
    file_path = f"{settings.output_base_path}/{timelapse.file_path}"

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timelapse video file not found on disk",
        )

    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=os.path.basename(timelapse.file_path),
    )


@router.get("/{timelapse_id}/download")
async def download_timelapse(
    timelapse_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """
    Download timelapse video file.
    """
    result = await db.execute(select(Timelapse).where(Timelapse.id == timelapse_id))
    timelapse = result.scalar_one_or_none()

    if timelapse is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timelapse not found",
        )

    if not timelapse.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timelapse video file not available",
        )

    settings = get_settings()
    file_path = f"{settings.output_base_path}/{timelapse.file_path}"

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timelapse video file not found on disk",
        )

    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=os.path.basename(timelapse.file_path),
        headers={"Content-Disposition": f"attachment; filename={os.path.basename(timelapse.file_path)}"},
    )


@router.delete("/{timelapse_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timelapse(
    timelapse_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a timelapse and its video file.
    """
    result = await db.execute(select(Timelapse).where(Timelapse.id == timelapse_id))
    timelapse = result.scalar_one_or_none()

    if timelapse is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timelapse not found",
        )

    # Delete video file
    if timelapse.file_path:
        settings = get_settings()
        file_path = f"{settings.output_base_path}/{timelapse.file_path}"
        if os.path.exists(file_path):
            os.remove(file_path)

    await db.delete(timelapse)
    await db.commit()


@router.post("/camera/{camera_id}", response_model=TimelapseResponse)
async def create_timelapse(
    camera_id: UUID,
    request: TimelapseCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TimelapseResponse:
    """
    Trigger timelapse generation for a camera.
    """
    # Verify camera exists
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()

    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found",
        )

    # Default to yesterday
    date_start = request.date_start or (date.today() - timedelta(days=1))
    date_end = request.date_end or date_start

    # Check if timelapse already exists
    existing = await db.execute(
        select(Timelapse).where(
            Timelapse.camera_id == camera_id,
            Timelapse.type == "daily",
            Timelapse.date_start == date_start,
            Timelapse.date_end == date_end,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Timelapse already exists for this date range",
        )

    settings = get_settings()

    # Create timelapse record
    timelapse = Timelapse(
        camera_id=camera_id,
        type="daily" if date_start == date_end else "multiday",
        date_start=date_start,
        date_end=date_end,
        frame_rate=request.frame_rate or settings.default_frame_rate,
        crf=request.crf or settings.default_crf,
        pixel_format=request.pixel_format or settings.default_pixel_format,
        status="pending",
    )

    db.add(timelapse)
    await db.commit()
    await db.refresh(timelapse)

    # TODO: Trigger async timelapse generation task

    return TimelapseResponse.model_validate(timelapse)


@router.get("/camera/{camera_id}", response_model=TimelapseListResponse)
async def list_camera_timelapses(
    camera_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TimelapseListResponse:
    """
    List timelapses for a specific camera.
    """
    # Verify camera exists
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found",
        )

    return await list_timelapses(
        camera_id=camera_id,
        timelapse_type=None,
        status_filter=None,
        page=page,
        per_page=per_page,
        db=db,
        current_user=current_user,
    )
