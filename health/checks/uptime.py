"""
Uptime Tracker

Track camera uptime and health statistics.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.camera import Camera
from api.models.camera_health import CameraHealth

logger = logging.getLogger(__name__)


class UptimeTracker:
    """Track camera uptime and health metrics."""

    async def record_check(
        self,
        db: AsyncSession,
        camera: Camera,
        is_reachable: bool,
        response_time_ms: Optional[int] = None,
        is_image_blank: Optional[bool] = None,
        is_image_frozen: Optional[bool] = None,
        error_message: Optional[str] = None,
    ) -> CameraHealth:
        """
        Record a health check result.

        Args:
            db: Database session
            camera: Camera that was checked
            is_reachable: Whether camera is reachable
            response_time_ms: Response time in milliseconds
            is_image_blank: Whether image appears blank
            is_image_frozen: Whether image appears frozen
            error_message: Error message if check failed

        Returns:
            Created CameraHealth record
        """
        health_record = CameraHealth(
            camera_id=camera.id,
            is_reachable=is_reachable,
            response_time_ms=response_time_ms,
            is_image_blank=is_image_blank,
            is_image_frozen=is_image_frozen,
            error_message=error_message,
            checked_at=datetime.now(timezone.utc),
        )

        db.add(health_record)
        await db.commit()
        await db.refresh(health_record)

        return health_record

    async def get_uptime_percentage(
        self,
        db: AsyncSession,
        camera: Camera,
        hours: int = 24,
    ) -> float:
        """
        Calculate uptime percentage for a camera.

        Args:
            db: Database session
            camera: Camera to check
            hours: Number of hours to look back

        Returns:
            Uptime percentage (0-100)
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Count total checks
        total_result = await db.execute(
            select(func.count(CameraHealth.id)).where(
                CameraHealth.camera_id == camera.id,
                CameraHealth.checked_at >= cutoff,
            )
        )
        total_checks = total_result.scalar() or 0

        if total_checks == 0:
            return 100.0  # No data, assume 100%

        # Count online checks
        online_result = await db.execute(
            select(func.count(CameraHealth.id)).where(
                CameraHealth.camera_id == camera.id,
                CameraHealth.checked_at >= cutoff,
                CameraHealth.is_reachable == True,
            )
        )
        online_checks = online_result.scalar() or 0

        return (online_checks / total_checks) * 100

    async def get_average_response_time(
        self,
        db: AsyncSession,
        camera: Camera,
        hours: int = 24,
    ) -> Optional[float]:
        """
        Calculate average response time for a camera.

        Args:
            db: Database session
            camera: Camera to check
            hours: Number of hours to look back

        Returns:
            Average response time in ms or None if no data
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        result = await db.execute(
            select(func.avg(CameraHealth.response_time_ms)).where(
                CameraHealth.camera_id == camera.id,
                CameraHealth.checked_at >= cutoff,
                CameraHealth.is_reachable == True,
                CameraHealth.response_time_ms.isnot(None),
            )
        )

        return result.scalar()

    async def get_health_history(
        self,
        db: AsyncSession,
        camera: Camera,
        hours: int = 24,
        limit: int = 100,
    ) -> list[CameraHealth]:
        """
        Get health check history for a camera.

        Args:
            db: Database session
            camera: Camera to get history for
            hours: Number of hours to look back
            limit: Maximum records to return

        Returns:
            List of CameraHealth records
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        result = await db.execute(
            select(CameraHealth)
            .where(
                CameraHealth.camera_id == camera.id,
                CameraHealth.checked_at >= cutoff,
            )
            .order_by(CameraHealth.checked_at.desc())
            .limit(limit)
        )

        return list(result.scalars().all())

    async def get_downtime_periods(
        self,
        db: AsyncSession,
        camera: Camera,
        hours: int = 24,
    ) -> list[dict]:
        """
        Get periods when camera was offline.

        Args:
            db: Database session
            camera: Camera to check
            hours: Number of hours to look back

        Returns:
            List of downtime period dictionaries
        """
        history = await self.get_health_history(
            db=db,
            camera=camera,
            hours=hours,
            limit=1000,
        )

        if not history:
            return []

        # Reverse to chronological order
        history = list(reversed(history))

        downtime_periods = []
        current_downtime_start = None

        for record in history:
            if not record.is_online:
                if current_downtime_start is None:
                    current_downtime_start = record.checked_at
            else:
                if current_downtime_start is not None:
                    downtime_periods.append(
                        {
                            "start": current_downtime_start,
                            "end": record.checked_at,
                            "duration_seconds": (
                                record.checked_at - current_downtime_start
                            ).total_seconds(),
                        }
                    )
                    current_downtime_start = None

        # Handle ongoing downtime
        if current_downtime_start is not None:
            downtime_periods.append(
                {
                    "start": current_downtime_start,
                    "end": None,
                    "duration_seconds": (
                        datetime.now(timezone.utc) - current_downtime_start
                    ).total_seconds(),
                }
            )

        return downtime_periods

    async def cleanup_old_records(
        self,
        db: AsyncSession,
        days: int = 30,
    ) -> int:
        """
        Delete old health records.

        Args:
            db: Database session
            days: Keep records newer than this many days

        Returns:
            Number of records deleted
        """
        from sqlalchemy import delete

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        result = await db.execute(delete(CameraHealth).where(CameraHealth.checked_at < cutoff))
        await db.commit()

        deleted = result.rowcount
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old health records")

        return deleted
