"""
Multi-day Timelapse Service

API-accessible service for multi-day timelapse operations.
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.models.camera import Camera
from api.models.image import Image
from api.models.multiday_config import MultidayConfig
from api.services.storage import StorageService

logger = logging.getLogger(__name__)


class MultidayTimelapseService:
    """Service for multi-day timelapse operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.storage = StorageService()

    async def get_configs_for_camera(
        self,
        camera_id: str,
    ) -> List[MultidayConfig]:
        """
        Get all multi-day configs for a camera.

        Args:
            camera_id: Camera UUID

        Returns:
            List of MultidayConfig objects
        """
        result = await self.db.execute(
            select(MultidayConfig).where(MultidayConfig.camera_id == camera_id)
        )
        return list(result.scalars().all())

    async def get_all_enabled_configs(self) -> List[MultidayConfig]:
        """
        Get all enabled multi-day configs.

        Returns:
            List of enabled MultidayConfig objects
        """
        result = await self.db.execute(
            select(MultidayConfig)
            .join(Camera)
            .where(
                MultidayConfig.is_enabled == True,
                Camera.is_active == True,
            )
        )
        return list(result.scalars().all())

    async def select_images_for_config(
        self,
        config: MultidayConfig,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Image]:
        """
        Select images for a multi-day timelapse based on config.

        Args:
            config: MultidayConfig to use
            start_date: Optional start date override
            end_date: Optional end date override

        Returns:
            List of selected images
        """
        if end_date is None:
            end_date = date.today() - timedelta(days=1)
        if start_date is None:
            start_date = end_date - timedelta(days=config.days_to_include - 1)

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        # Get all images in date range
        result = await self.db.execute(
            select(Image)
            .where(
                Image.camera_id == config.camera_id,
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
            count = min(config.images_per_hour, len(images))

            if count == len(images):
                selected.extend(images)
            else:
                step = len(images) / count
                for i in range(count):
                    idx = int(i * step)
                    selected.append(images[idx])

        return selected

    async def protect_images(self, images: List[Image]) -> int:
        """
        Mark images as protected from cleanup.

        Args:
            images: List of images to protect

        Returns:
            Number of images protected
        """
        count = 0
        for image in images:
            if not image.is_protected:
                image.is_protected = True
                count += 1

        await self.db.commit()
        return count

    async def unprotect_images(self, images: List[Image]) -> int:
        """
        Remove protection from images.

        Args:
            images: List of images to unprotect

        Returns:
            Number of images unprotected
        """
        count = 0
        for image in images:
            if image.is_protected:
                image.is_protected = False
                count += 1

        await self.db.commit()
        return count

    async def get_protected_image_count(
        self,
        camera_id: Optional[str] = None,
    ) -> int:
        """
        Get count of protected images.

        Args:
            camera_id: Optional camera to filter by

        Returns:
            Number of protected images
        """
        from sqlalchemy import func

        query = select(func.count(Image.id)).where(Image.is_protected == True)
        if camera_id:
            query = query.where(Image.camera_id == camera_id)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def preview_multiday_timelapse(
        self,
        config: MultidayConfig,
    ) -> dict:
        """
        Preview what a multi-day timelapse would include.

        Args:
            config: MultidayConfig to preview

        Returns:
            Dictionary with preview information
        """
        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=config.days_to_include - 1)

        images = await self.select_images_for_config(
            config=config,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "config_id": str(config.id),
            "camera_id": str(config.camera_id),
            "start_date": str(start_date),
            "end_date": str(end_date),
            "days_included": config.days_to_include,
            "images_per_hour": config.images_per_hour,
            "expected_images": config.images_per_hour * 24 * config.days_to_include,
            "actual_images": len(images),
            "expected_duration_seconds": len(images) / config.frame_rate,
            "frame_rate": config.frame_rate,
            "crf": config.crf,
            "pixel_format": config.pixel_format,
        }
