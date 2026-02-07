"""
Health Status Router

Camera health monitoring endpoints.
"""

from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.database import get_db
from api.models.camera import Camera
from api.models.camera_health import CameraHealth
from api.models.user import User
from api.schemas.settings import CameraHealthHistoryResponse, CameraHealthResponse

router = APIRouter(prefix="/health", tags=["Camera Health"])


@router.get("/cameras", response_model=List[CameraHealthResponse])
async def get_all_cameras_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[CameraHealthResponse]:
    """
    Get health status for all cameras.
    """
    # Get all cameras
    result = await db.execute(select(Camera).order_by(Camera.name))
    cameras = result.scalars().all()

    health_responses = []
    for camera in cameras:
        # Get latest health check
        health_result = await db.execute(
            select(CameraHealth)
            .where(CameraHealth.camera_id == camera.id)
            .order_by(CameraHealth.checked_at.desc())
            .limit(1)
        )
        latest_health = health_result.scalar_one_or_none()

        health_responses.append(
            CameraHealthResponse(
                camera_id=camera.id,
                camera_name=camera.name,
                is_reachable=latest_health.is_reachable if latest_health else False,
                response_time_ms=latest_health.response_time_ms if latest_health else None,
                is_image_blank=latest_health.is_image_blank if latest_health else None,
                is_image_frozen=latest_health.is_image_frozen if latest_health else None,
                last_check=latest_health.checked_at if latest_health else None,
                consecutive_failures=camera.consecutive_errors,
                is_healthy=latest_health.is_healthy if latest_health else False,
            )
        )

    return health_responses


@router.get("/cameras/{camera_id}", response_model=CameraHealthResponse)
async def get_camera_health(
    camera_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CameraHealthResponse:
    """
    Get health status for a specific camera.
    """
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()

    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")

    # Get latest health check
    health_result = await db.execute(
        select(CameraHealth)
        .where(CameraHealth.camera_id == camera_id)
        .order_by(CameraHealth.checked_at.desc())
        .limit(1)
    )
    latest_health = health_result.scalar_one_or_none()

    return CameraHealthResponse(
        camera_id=camera.id,
        camera_name=camera.name,
        is_reachable=latest_health.is_reachable if latest_health else False,
        response_time_ms=latest_health.response_time_ms if latest_health else None,
        is_image_blank=latest_health.is_image_blank if latest_health else None,
        is_image_frozen=latest_health.is_image_frozen if latest_health else None,
        last_check=latest_health.checked_at if latest_health else None,
        consecutive_failures=camera.consecutive_errors,
        is_healthy=latest_health.is_healthy if latest_health else False,
    )


@router.get("/cameras/{camera_id}/history", response_model=CameraHealthHistoryResponse)
async def get_camera_health_history(
    camera_id: UUID,
    hours: int = Query(24, ge=1, le=168, description="Hours of history to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CameraHealthHistoryResponse:
    """
    Get health check history for a camera.
    """
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Camera not found")

    # Get health checks from the last N hours
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    result = await db.execute(
        select(CameraHealth)
        .where(
            CameraHealth.camera_id == camera_id,
            CameraHealth.checked_at >= cutoff,
        )
        .order_by(CameraHealth.checked_at.desc())
    )
    checks = result.scalars().all()

    # Calculate uptime percentage
    total_checks = len(checks)
    successful_checks = sum(1 for c in checks if c.is_reachable)
    uptime_percent = (successful_checks / total_checks * 100) if total_checks > 0 else 0

    # Calculate average response time
    response_times = [c.response_time_ms for c in checks if c.response_time_ms is not None]
    avg_response_time = sum(response_times) / len(response_times) if response_times else None

    return CameraHealthHistoryResponse(
        camera_id=camera_id,
        checks=[
            {
                "checked_at": c.checked_at.isoformat(),
                "is_reachable": c.is_reachable,
                "response_time_ms": c.response_time_ms,
                "is_image_blank": c.is_image_blank,
                "is_image_frozen": c.is_image_frozen,
            }
            for c in checks
        ],
        uptime_percent=uptime_percent,
        avg_response_time_ms=avg_response_time,
    )


@router.get("/summary")
async def get_health_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get overall health summary.
    """
    # Count cameras
    result = await db.execute(select(func.count(Camera.id)))
    total_cameras = result.scalar() or 0

    # Get cameras with issues
    result = await db.execute(
        select(Camera).where(Camera.consecutive_errors >= 3)
    )
    cameras_with_issues = len(result.scalars().all())

    return {
        "total_cameras": total_cameras,
        "cameras_healthy": total_cameras - cameras_with_issues,
        "cameras_with_issues": cameras_with_issues,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
