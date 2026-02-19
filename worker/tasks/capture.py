"""
Capture Task

Scheduled task for capturing images from all active cameras.
"""

import logging
from datetime import date, datetime, timezone

from api.config import get_settings
from api.database import get_db_context
from api.services.capture import CaptureService
from api.services.multiday_timelapse import MultidayTimelapseService
from api.services.notification import NotificationService

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_capture_cycle() -> None:
    """
    Run a capture cycle for all cameras due for capture.

    This task:
    1. Identifies cameras due for capture based on their intervals
    2. Captures images concurrently
    3. Sends notifications for consecutive failures
    """
    start_time = datetime.now(timezone.utc)
    logger.debug(f"Starting capture cycle at {start_time}")

    async with get_db_context() as db:
        capture_service = CaptureService(db)
        notification_service = NotificationService(db)
        multiday_service = MultidayTimelapseService(db)

        # Get cameras due for capture
        cameras = await capture_service.get_cameras_due_for_capture()

        if not cameras:
            logger.debug("No cameras due for capture")
            return

        logger.info(f"Capturing from {len(cameras)} camera(s)")

        # Capture from all cameras
        results = await capture_service.capture_all(cameras)

        # Process results
        successful = 0
        failed = 0
        cameras_captured = set()

        for result in results:
            if result.success:
                successful += 1
                cameras_captured.add(result.camera.id)
            else:
                failed += 1

                # Check if we should notify about failures
                if result.camera.consecutive_errors >= settings.min_failures_before_alert:
                    await notification_service.notify_capture_failure(
                        camera_name=result.camera.name,
                        error=result.error or "Unknown error",
                        consecutive_failures=result.camera.consecutive_errors,
                    )

        # Protect images for prospective collections
        today = date.today()
        for camera_id in cameras_captured:
            try:
                protected = await multiday_service.protect_images_for_prospective(
                    camera_id=camera_id,
                    captured_date=today,
                )
                if protected > 0:
                    logger.debug(f"Protected {protected} images for camera {camera_id}")
            except Exception as e:
                logger.error(f"Error protecting images for camera {camera_id}: {e}")

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(
            f"Capture cycle complete: {successful} successful, {failed} failed in {elapsed:.2f}s"
        )
