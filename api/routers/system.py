"""
System Router

System information and health check endpoints.
"""

import os
import sys
import time
from datetime import datetime, timezone

import redis.asyncio as redis
from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from api import __version__
from api.config import get_settings
from api.database import get_db
from api.models.camera import Camera
from api.models.image import Image
from api.models.timelapse import Timelapse
from api.schemas.settings import (
    HealthCheckResponse,
    StorageInfoResponse,
    SystemInfoResponse,
)

router = APIRouter(prefix="/system", tags=["System"])

# Track startup time
_startup_time = time.time()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    db: AsyncSession = Depends(get_db),
) -> HealthCheckResponse:
    """
    Health check endpoint for container orchestration.
    """
    settings = get_settings()

    # Check database
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    # Check Redis
    redis_ok = False
    try:
        r = redis.from_url(settings.redis_url)
        await r.ping()
        redis_ok = True
        await r.close()
    except Exception:
        pass

    status = "healthy" if (db_ok and redis_ok) else "unhealthy"

    return HealthCheckResponse(
        status=status,
        database=db_ok,
        redis=redis_ok,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/info", response_model=SystemInfoResponse)
async def system_info(
    db: AsyncSession = Depends(get_db),
) -> SystemInfoResponse:
    """
    Get system information.
    """
    settings = get_settings()

    # Check database
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    # Check Redis
    redis_ok = False
    try:
        r = redis.from_url(settings.redis_url)
        await r.ping()
        redis_ok = True
        await r.close()
    except Exception:
        pass

    # Get counts
    cameras_count = 0
    images_count = 0
    timelapses_count = 0

    try:
        result = await db.execute(select(func.count(Camera.id)))
        cameras_count = result.scalar() or 0

        result = await db.execute(select(func.count(Image.id)))
        images_count = result.scalar() or 0

        result = await db.execute(select(func.count(Timelapse.id)))
        timelapses_count = result.scalar() or 0
    except Exception:
        pass

    # Determine overall API status
    if db_ok and redis_ok:
        status = "healthy"
    elif db_ok or redis_ok:
        status = "degraded"
    else:
        status = "unhealthy"

    # Check worker status via Redis heartbeat
    worker_status = "unknown"
    try:
        r = redis.from_url(settings.redis_url)
        heartbeat = await r.get("worker:heartbeat")
        if heartbeat:
            # Check if heartbeat is recent (within 2 minutes)
            last_beat = float(heartbeat)
            if time.time() - last_beat < 120:
                worker_status = "healthy"
            else:
                worker_status = "unhealthy"
        await r.close()
    except Exception:
        pass

    return SystemInfoResponse(
        version=__version__,
        status=status,
        worker_status=worker_status,
        uptime_seconds=time.time() - _startup_time,
        python_version=sys.version,
        database_connected=db_ok,
        redis_connected=redis_ok,
        cameras_count=cameras_count,
        images_count=images_count,
        timelapses_count=timelapses_count,
    )


@router.get("/storage", response_model=StorageInfoResponse)
async def storage_info(
    db: AsyncSession = Depends(get_db),
) -> StorageInfoResponse:
    """
    Get storage usage information.
    """
    settings = get_settings()

    # Get disk usage
    try:
        stat = os.statvfs(settings.output_base_path)
        total_bytes = stat.f_blocks * stat.f_frsize
        free_bytes = stat.f_bavail * stat.f_frsize
        used_bytes = total_bytes - free_bytes
        percent_used = (used_bytes / total_bytes) * 100 if total_bytes > 0 else 0
    except Exception:
        total_bytes = 0
        used_bytes = 0
        free_bytes = 0
        percent_used = 0

    # Get image stats
    images_size = 0
    images_count = 0
    try:
        result = await db.execute(select(func.sum(Image.file_size), func.count(Image.id)))
        row = result.one()
        images_size = row[0] or 0
        images_count = row[1] or 0
    except Exception:
        pass

    # Get video stats
    videos_size = 0
    videos_count = 0
    try:
        result = await db.execute(
            select(func.sum(Timelapse.file_size), func.count(Timelapse.id)).where(
                Timelapse.file_size.isnot(None)
            )
        )
        row = result.one()
        videos_size = row[0] or 0
        videos_count = row[1] or 0
    except Exception:
        pass

    return StorageInfoResponse(
        total_bytes=total_bytes,
        used_bytes=used_bytes,
        free_bytes=free_bytes,
        percent_used=percent_used,
        images_size_bytes=images_size,
        videos_size_bytes=videos_size,
        images_count=images_count,
        videos_count=videos_count,
    )
