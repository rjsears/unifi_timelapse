"""
Cleanup Service

Automatic cleanup of old images and videos.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.models.camera import Camera
from api.models.cleanup_log import CleanupLog
from api.models.image import Image
from api.models.timelapse import Timelapse
from api.services.storage import StorageService

logger = logging.getLogger(__name__)


class CleanupService:
    """Service for cleaning up old files."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.storage = StorageService()

    async def cleanup_old_images(
        self,
        camera_id: Optional[str] = None,
        retention_days: Optional[int] = None,
    ) -> CleanupLog:
        """
        Clean up images older than retention period.

        Respects is_protected flag and skips protected images.

        Args:
            camera_id: Optional camera ID to limit cleanup
            retention_days: Optional retention days override

        Returns:
            CleanupLog record
        """
        retention_days = retention_days or self.settings.retention_days_images
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

        # Build query for images to delete
        query = select(Image).where(
            Image.captured_at < cutoff_date,
            Image.is_protected == False,
        )

        if camera_id:
            query = query.where(Image.camera_id == camera_id)

        result = await self.db.execute(query)
        images_to_delete = result.scalars().all()

        # Count protected images that would have been deleted
        protected_query = select(func.count(Image.id)).where(
            Image.captured_at < cutoff_date,
            Image.is_protected == True,
        )
        if camera_id:
            protected_query = protected_query.where(Image.camera_id == camera_id)

        protected_result = await self.db.execute(protected_query)
        protected_count = protected_result.scalar() or 0

        # Delete files and records
        files_deleted = 0
        bytes_freed = 0

        for image in images_to_delete:
            try:
                # Delete file
                if self.storage.delete_file(image.file_path):
                    bytes_freed += image.file_size or 0
                    files_deleted += 1

                # Delete database record
                await self.db.delete(image)

            except Exception as e:
                logger.warning(f"Failed to delete image {image.id}: {e}")

        await self.db.commit()

        # Create cleanup log
        cleanup_log = CleanupLog(
            type="images",
            camera_id=camera_id,
            files_deleted=files_deleted,
            bytes_freed=bytes_freed,
            protected_skipped=protected_count,
            executed_at=datetime.now(timezone.utc),
        )
        self.db.add(cleanup_log)
        await self.db.commit()

        logger.info(
            f"Cleanup complete: {files_deleted} images deleted, "
            f"{bytes_freed / 1024 / 1024:.2f} MB freed, "
            f"{protected_count} protected skipped"
        )

        return cleanup_log

    async def cleanup_old_videos(
        self,
        camera_id: Optional[str] = None,
        retention_days: Optional[int] = None,
    ) -> CleanupLog:
        """
        Clean up videos older than retention period.

        Args:
            camera_id: Optional camera ID to limit cleanup
            retention_days: Optional retention days override

        Returns:
            CleanupLog record
        """
        retention_days = retention_days or self.settings.retention_days_videos
        cutoff_date = datetime.now(timezone.utc).date() - timedelta(days=retention_days)

        # Build query for timelapses to delete
        query = select(Timelapse).where(
            Timelapse.date_end < cutoff_date,
            Timelapse.status == "completed",
        )

        if camera_id:
            query = query.where(Timelapse.camera_id == camera_id)

        result = await self.db.execute(query)
        videos_to_delete = result.scalars().all()

        # Delete files and records
        files_deleted = 0
        bytes_freed = 0

        for timelapse in videos_to_delete:
            try:
                # Delete file
                if timelapse.file_path and self.storage.delete_file(timelapse.file_path):
                    bytes_freed += timelapse.file_size or 0
                    files_deleted += 1

                # Delete database record
                await self.db.delete(timelapse)

            except Exception as e:
                logger.warning(f"Failed to delete timelapse {timelapse.id}: {e}")

        await self.db.commit()

        # Create cleanup log
        cleanup_log = CleanupLog(
            type="videos",
            camera_id=camera_id,
            files_deleted=files_deleted,
            bytes_freed=bytes_freed,
            protected_skipped=0,
            executed_at=datetime.now(timezone.utc),
        )
        self.db.add(cleanup_log)
        await self.db.commit()

        logger.info(
            f"Video cleanup complete: {files_deleted} videos deleted, "
            f"{bytes_freed / 1024 / 1024:.2f} MB freed"
        )

        return cleanup_log

    async def cleanup_after_timelapse(
        self,
        timelapse: Timelapse,
    ) -> CleanupLog:
        """
        Clean up images after successful timelapse generation.

        Only deletes non-protected images that were included in the timelapse.

        Args:
            timelapse: Completed timelapse

        Returns:
            CleanupLog record
        """
        if timelapse.status != "completed":
            raise ValueError("Can only cleanup after completed timelapse")

        # Get images for this timelapse
        result = await self.db.execute(
            select(Image).where(
                Image.included_in_timelapse_id == timelapse.id,
                Image.is_protected == False,
            )
        )
        images_to_delete = result.scalars().all()

        # Count protected
        protected_result = await self.db.execute(
            select(func.count(Image.id)).where(
                Image.included_in_timelapse_id == timelapse.id,
                Image.is_protected == True,
            )
        )
        protected_count = protected_result.scalar() or 0

        # Delete files and records
        files_deleted = 0
        bytes_freed = 0

        for image in images_to_delete:
            try:
                if self.storage.delete_file(image.file_path):
                    bytes_freed += image.file_size or 0
                    files_deleted += 1

                await self.db.delete(image)

            except Exception as e:
                logger.warning(f"Failed to delete image {image.id}: {e}")

        await self.db.commit()

        # Create cleanup log
        cleanup_log = CleanupLog(
            type="timelapse_cleanup",
            camera_id=timelapse.camera_id,
            files_deleted=files_deleted,
            bytes_freed=bytes_freed,
            protected_skipped=protected_count,
            executed_at=datetime.now(timezone.utc),
        )
        self.db.add(cleanup_log)
        await self.db.commit()

        logger.info(
            f"Post-timelapse cleanup: {files_deleted} images deleted, "
            f"{protected_count} protected skipped"
        )

        return cleanup_log
