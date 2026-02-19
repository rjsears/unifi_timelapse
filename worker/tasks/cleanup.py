"""
Cleanup Task

Scheduled task for cleaning up old images and videos.
"""

import logging
from datetime import datetime, timezone

from api.config import get_settings
from api.database import get_db_context
from api.services.cleanup import CleanupService
from api.services.notification import NotificationService
from api.services.storage import StorageService

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_cleanup() -> None:
    """
    Run cleanup for old images and videos.

    This task:
    1. Deletes images older than retention period (respects is_protected)
    2. Deletes videos older than retention period
    3. Checks storage usage and sends warnings if needed
    """
    start_time = datetime.now(timezone.utc)
    logger.info(f"Starting cleanup at {start_time}")

    async with get_db_context() as db:
        cleanup_service = CleanupService(db)
        notification_service = NotificationService(db)
        storage_service = StorageService()

        # Cleanup old images
        logger.info(f"Cleaning up images older than {settings.retention_days_images} days")
        image_log = await cleanup_service.cleanup_old_images()
        logger.info(
            f"Image cleanup: {image_log.files_deleted} files deleted, "
            f"{image_log.bytes_freed / 1024 / 1024:.2f} MB freed, "
            f"{image_log.protected_skipped} protected skipped"
        )

        # Cleanup old videos
        logger.info(f"Cleaning up videos older than {settings.retention_days_videos} days")
        video_log = await cleanup_service.cleanup_old_videos()
        logger.info(
            f"Video cleanup: {video_log.files_deleted} files deleted, "
            f"{video_log.bytes_freed / 1024 / 1024:.2f} MB freed"
        )

        # Check storage usage
        disk_usage = storage_service.get_disk_usage()
        percent_used = disk_usage["percent_used"]

        # Warn if storage is getting full (>85%)
        if percent_used > 85:
            logger.warning(f"Storage is {percent_used:.1f}% full!")
            await notification_service.notify_storage_warning(
                percent_used=percent_used,
                free_bytes=disk_usage["free_bytes"],
            )
        else:
            logger.info(f"Storage usage: {percent_used:.1f}%")

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        total_freed = image_log.bytes_freed + video_log.bytes_freed
        logger.info(f"Cleanup complete: {total_freed / 1024 / 1024:.2f} MB freed in {elapsed:.2f}s")


async def run_cleanup_for_camera(camera_id: str) -> None:
    """
    Run cleanup for a specific camera.

    Args:
        camera_id: Camera UUID to cleanup
    """
    logger.info(f"Running cleanup for camera {camera_id}")

    async with get_db_context() as db:
        cleanup_service = CleanupService(db)

        # Cleanup images for this camera
        image_log = await cleanup_service.cleanup_old_images(camera_id=camera_id)
        logger.info(
            f"Camera image cleanup: {image_log.files_deleted} files deleted, "
            f"{image_log.bytes_freed / 1024 / 1024:.2f} MB freed"
        )

        # Cleanup videos for this camera
        video_log = await cleanup_service.cleanup_old_videos(camera_id=camera_id)
        logger.info(
            f"Camera video cleanup: {video_log.files_deleted} files deleted, "
            f"{video_log.bytes_freed / 1024 / 1024:.2f} MB freed"
        )
