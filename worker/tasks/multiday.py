"""
Multi-day Timelapse Task

Scheduled task for generating multi-day summary timelapse videos.
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import List

from sqlalchemy import select

from api.config import get_settings
from api.database import get_db_context
from api.models.camera import Camera
from api.models.image import Image
from api.models.multiday_config import MultidayConfig
from api.models.timelapse import Timelapse
from api.services.notification import NotificationService
from api.services.storage import StorageService
from worker.ffmpeg.encoder import FFMPEGEncoder

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_multiday_timelapse_generation() -> None:
    """
    Generate multi-day timelapse videos for all configured cameras.

    This task:
    1. Finds all cameras with multi-day timelapse configs
    2. Selects X images per hour over Y days
    3. Protects selected images from cleanup
    4. Generates a summary timelapse
    5. Sends notifications on completion
    """
    start_time = datetime.now(timezone.utc)
    logger.info(f"Starting multi-day timelapse generation at {start_time}")

    async with get_db_context() as db:
        # Get all active multiday configs
        result = await db.execute(
            select(MultidayConfig)
            .join(Camera)
            .where(
                MultidayConfig.is_enabled == True,
                Camera.is_active == True,
            )
        )
        configs = result.scalars().all()

        if not configs:
            logger.info("No multi-day timelapse configs found")
            return

        logger.info(f"Processing {len(configs)} multi-day config(s)")

        notification_service = NotificationService(db)
        storage_service = StorageService()
        encoder = FFMPEGEncoder()

        successful = 0
        failed = 0

        for config in configs:
            try:
                logger.info(
                    f"Generating multi-day timelapse for camera {config.camera_id}"
                )

                # Get camera
                camera_result = await db.execute(
                    select(Camera).where(Camera.id == config.camera_id)
                )
                camera = camera_result.scalar_one_or_none()

                if not camera:
                    logger.warning(f"Camera {config.camera_id} not found")
                    continue

                # Calculate date range
                end_date = date.today() - timedelta(days=1)
                start_date = end_date - timedelta(days=config.days_to_include - 1)

                # Select images for the timelapse
                selected_images = await select_images_for_multiday(
                    db=db,
                    camera_id=config.camera_id,
                    start_date=start_date,
                    end_date=end_date,
                    images_per_hour=config.images_per_hour,
                )

                if not selected_images:
                    logger.warning("No images found for multi-day timelapse")
                    continue

                logger.info(f"Selected {len(selected_images)} images for timelapse")

                # Mark images as protected
                for image in selected_images:
                    image.is_protected = True
                await db.commit()

                # Create timelapse record
                timelapse = Timelapse(
                    camera_id=camera.id,
                    type="multiday",
                    date_start=start_date,
                    date_end=end_date,
                    frame_rate=config.frame_rate or settings.default_frame_rate,
                    crf=config.crf or settings.default_crf,
                    pixel_format=config.pixel_format or settings.default_pixel_format,
                    status="processing",
                    started_at=datetime.now(timezone.utc),
                )
                db.add(timelapse)
                await db.commit()
                await db.refresh(timelapse)

                try:
                    # Generate the video
                    output_dir = storage_service.get_video_dir(camera.name, "summary")
                    filename = storage_service.get_summary_video_filename(
                        datetime.combine(start_date, datetime.min.time()),
                        datetime.combine(end_date, datetime.min.time()),
                    )
                    output_path = output_dir / filename

                    # Get image paths
                    image_paths = [
                        f"{settings.output_base_path}/{img.file_path}"
                        for img in selected_images
                    ]

                    # Encode video
                    await encoder.encode_from_images(
                        image_paths=image_paths,
                        output_path=str(output_path),
                        frame_rate=timelapse.frame_rate,
                        crf=timelapse.crf,
                        pixel_format=timelapse.pixel_format,
                    )

                    # Update timelapse record
                    timelapse.file_path = storage_service.get_relative_video_path(
                        camera.name, "summary", filename
                    )
                    timelapse.file_size = output_path.stat().st_size
                    timelapse.frame_count = len(selected_images)
                    timelapse.duration_seconds = len(selected_images) / timelapse.frame_rate
                    timelapse.status = "completed"
                    timelapse.completed_at = datetime.now(timezone.utc)

                    # Link images to timelapse
                    for image in selected_images:
                        image.included_in_timelapse_id = timelapse.id

                    await db.commit()

                    successful += 1

                    # Send notification
                    await notification_service.notify_timelapse_complete(
                        camera_name=camera.name,
                        timelapse_type="multi-day",
                        date_range=f"{start_date} to {end_date}",
                        frame_count=len(selected_images),
                    )

                    logger.info(
                        f"Multi-day timelapse completed for {camera.name}: "
                        f"{len(selected_images)} frames"
                    )

                except Exception as e:
                    timelapse.status = "failed"
                    timelapse.error_message = str(e)
                    await db.commit()
                    raise

            except Exception as e:
                failed += 1
                logger.exception(
                    f"Error generating multi-day timelapse for config {config.id}: {e}"
                )

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(
            f"Multi-day timelapse generation complete: {successful} successful, "
            f"{failed} failed in {elapsed:.2f}s"
        )


async def select_images_for_multiday(
    db,
    camera_id: str,
    start_date: date,
    end_date: date,
    images_per_hour: int,
) -> List[Image]:
    """
    Select images for multi-day timelapse.

    Selects evenly distributed images across each hour of each day.

    Args:
        db: Database session
        camera_id: Camera UUID
        start_date: Start date
        end_date: End date
        images_per_hour: Number of images to select per hour

    Returns:
        List of selected images
    """
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    # Get all images in date range
    result = await db.execute(
        select(Image)
        .where(
            Image.camera_id == camera_id,
            Image.captured_at >= start_dt,
            Image.captured_at <= end_dt,
        )
        .order_by(Image.captured_at)
    )
    all_images = result.scalars().all()

    if not all_images:
        return []

    # Group images by hour
    hourly_buckets = {}
    for image in all_images:
        hour_key = image.captured_at.strftime("%Y%m%d%H")
        if hour_key not in hourly_buckets:
            hourly_buckets[hour_key] = []
        hourly_buckets[hour_key].append(image)

    # Select evenly distributed images from each hour
    selected = []
    for hour_key in sorted(hourly_buckets.keys()):
        images = hourly_buckets[hour_key]
        count = min(images_per_hour, len(images))

        if count == len(images):
            selected.extend(images)
        else:
            # Select evenly distributed images
            step = len(images) / count
            for i in range(count):
                idx = int(i * step)
                selected.append(images[idx])

    return selected
