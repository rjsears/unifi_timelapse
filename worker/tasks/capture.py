"""
Capture Task

Scheduled task for capturing images from all active cameras.
"""

import logging
from datetime import datetime, timezone

from api.config import get_settings
from api.database import get_db_context
from api.services.capture import CaptureService
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

        for result in results:
            if result.success:
                successful += 1
            else:
                failed += 1

                # Check if we should notify about failures
                if result.camera.consecutive_errors >= settings.min_failures_before_alert:
                    await notification_service.notify_capture_failure(
                        camera_name=result.camera.name,
                        error=result.error or "Unknown error",
                        consecutive_failures=result.camera.consecutive_errors,
                    )

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(
            f"Capture cycle complete: {successful} successful, {failed} failed "
            f"in {elapsed:.2f}s"
        )
