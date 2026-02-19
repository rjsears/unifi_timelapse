"""
Timelapse Task

Scheduled task for generating daily timelapse videos.
"""

import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from api.config import get_settings
from api.database import get_db_context
from api.models.camera import Camera
from api.models.timelapse import Timelapse
from api.services.cleanup import CleanupService
from api.services.notification import NotificationService
from api.services.timelapse import TimelapseService

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_daily_timelapse_generation() -> None:
    """
    Generate daily timelapse videos for all cameras.

    This task:
    1. Finds all cameras with timelapse enabled
    2. Generates a timelapse for yesterday's images
    3. Optionally cleans up images after timelapse
    4. Sends notifications on completion
    """
    start_time = datetime.now(timezone.utc)
    logger.info(f"Starting daily timelapse generation at {start_time}")

    # Generate timelapse for yesterday
    target_date = date.today() - timedelta(days=1)

    async with get_db_context() as db:
        # Get cameras with timelapse enabled
        result = await db.execute(
            select(Camera).where(
                Camera.is_active == True,
                Camera.timelapse_enabled == True,
            )
        )
        cameras = result.scalars().all()

        if not cameras:
            logger.info("No cameras with timelapse enabled")
            return

        logger.info(f"Processing {len(cameras)} camera(s) for date {target_date}")

        timelapse_service = TimelapseService(db)
        cleanup_service = CleanupService(db)
        notification_service = NotificationService(db)

        successful = 0
        failed = 0

        for camera in cameras:
            try:
                logger.info(f"Generating timelapse for {camera.name}")

                # Generate the timelapse
                timelapse = await timelapse_service.generate_daily_timelapse(
                    camera=camera,
                    target_date=target_date,
                )

                if timelapse.status == "completed":
                    successful += 1

                    # Send notification
                    await notification_service.notify_timelapse_complete(
                        camera_name=camera.name,
                        timelapse_type="daily",
                        date_range=str(target_date),
                        frame_count=timelapse.frame_count or 0,
                    )

                    # Cleanup images if enabled
                    if settings.cleanup_after_timelapse:
                        logger.info(f"Cleaning up images for {camera.name}")
                        await cleanup_service.cleanup_after_timelapse(timelapse)

                else:
                    failed += 1
                    logger.warning(f"Timelapse for {camera.name} failed: {timelapse.error_message}")

            except Exception as e:
                failed += 1
                logger.exception(f"Error generating timelapse for {camera.name}: {e}")

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(
            f"Daily timelapse generation complete: {successful} successful, "
            f"{failed} failed in {elapsed:.2f}s"
        )


async def generate_timelapse_for_camera(camera_id: str, target_date: date) -> None:
    """
    Generate a timelapse for a specific camera and date.

    This can be called manually or via API trigger.

    Args:
        camera_id: Camera UUID
        target_date: Date to generate timelapse for
    """
    logger.info(f"Manual timelapse request for camera {camera_id} on {target_date}")

    async with get_db_context() as db:
        # Get camera
        result = await db.execute(select(Camera).where(Camera.id == camera_id))
        camera = result.scalar_one_or_none()

        if not camera:
            logger.error(f"Camera {camera_id} not found")
            return

        timelapse_service = TimelapseService(db)
        notification_service = NotificationService(db)

        try:
            timelapse = await timelapse_service.generate_daily_timelapse(
                camera=camera,
                target_date=target_date,
            )

            if timelapse.status == "completed":
                await notification_service.notify_timelapse_complete(
                    camera_name=camera.name,
                    timelapse_type="daily",
                    date_range=str(target_date),
                    frame_count=timelapse.frame_count or 0,
                )
                logger.info(f"Timelapse generated successfully for {camera.name}")
            else:
                logger.warning(f"Timelapse generation failed: {timelapse.error_message}")

        except Exception as e:
            logger.exception(f"Error generating timelapse: {e}")


async def process_pending_timelapses() -> None:
    """
    Process any pending timelapse jobs.

    This picks up timelapses created via the API that haven't been
    processed yet. Runs periodically to handle manual timelapse requests.
    """
    async with get_db_context() as db:
        # Get pending timelapses
        result = await db.execute(
            select(Timelapse)
            .where(Timelapse.status == "pending")
            .order_by(Timelapse.created_at)
            .limit(5)  # Process up to 5 at a time
        )
        pending = result.scalars().all()

        if not pending:
            return

        logger.info(f"Processing {len(pending)} pending timelapse(s)")

        timelapse_service = TimelapseService(db)
        notification_service = NotificationService(db)

        for timelapse in pending:
            try:
                # Get camera
                camera_result = await db.execute(
                    select(Camera).where(Camera.id == timelapse.camera_id)
                )
                camera = camera_result.scalar_one_or_none()

                if not camera:
                    timelapse.status = "failed"
                    timelapse.error_message = "Camera not found"
                    await db.commit()
                    continue

                logger.info(
                    f"Processing pending timelapse for {camera.name} "
                    f"({timelapse.date_start} to {timelapse.date_end})"
                )

                # Generate the timelapse
                result = await timelapse_service.generate_daily_timelapse(
                    camera=camera,
                    target_date=timelapse.date_start,
                    frame_rate=timelapse.frame_rate,
                    crf=timelapse.crf,
                    pixel_format=timelapse.pixel_format,
                )

                if result.status == "completed":
                    await notification_service.notify_timelapse_complete(
                        camera_name=camera.name,
                        timelapse_type="daily",
                        date_range=str(timelapse.date_start),
                        frame_count=result.frame_count or 0,
                    )
                    logger.info(f"Pending timelapse completed for {camera.name}")
                else:
                    logger.warning(
                        f"Pending timelapse failed for {camera.name}: {result.error_message}"
                    )

            except Exception as e:
                logger.exception(f"Error processing pending timelapse: {e}")
                timelapse.status = "failed"
                timelapse.error_message = str(e)
                await db.commit()
