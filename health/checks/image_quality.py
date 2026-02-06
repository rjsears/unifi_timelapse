"""
Image Quality Checker

Check for blank and frozen camera images.
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Optional

from PIL import Image as PILImage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.models.camera import Camera
from api.models.image import Image

logger = logging.getLogger(__name__)
settings = get_settings()


class ImageQualityChecker:
    """Check camera image quality for issues."""

    def __init__(self):
        self.blank_threshold = settings.blank_threshold
        # Cache of recent image hashes for frozen detection
        self._image_hashes: dict[str, list[str]] = {}

    async def check_blank(
        self,
        db: AsyncSession,
        camera: Camera,
    ) -> bool:
        """
        Check if the most recent image is blank/dark.

        Args:
            db: Database session
            camera: Camera to check

        Returns:
            True if image appears blank
        """
        # Get most recent image
        result = await db.execute(
            select(Image)
            .where(Image.camera_id == camera.id)
            .order_by(Image.captured_at.desc())
            .limit(1)
        )
        image_record = result.scalar_one_or_none()

        if not image_record:
            return False

        # Load and analyze image
        try:
            image_path = f"{settings.output_base_path}/{image_record.file_path}"
            with open(image_path, "rb") as f:
                img = PILImage.open(f)
                return self._is_blank(img)

        except Exception as e:
            logger.warning(f"Failed to check image for {camera.name}: {e}")
            return False

    def _is_blank(self, img: PILImage.Image) -> bool:
        """
        Determine if an image is blank/dark.

        Uses standard deviation of pixel values to detect blank images.

        Args:
            img: PIL Image object

        Returns:
            True if image appears blank
        """
        try:
            # Convert to grayscale
            gray = img.convert("L")

            # Get pixel statistics
            pixels = list(gray.getdata())
            mean = sum(pixels) / len(pixels)

            # Calculate standard deviation
            variance = sum((p - mean) ** 2 for p in pixels) / len(pixels)
            std_dev = variance ** 0.5

            # Normalize to 0-1 range
            normalized_std = std_dev / 255

            is_blank = normalized_std < self.blank_threshold

            if is_blank:
                logger.debug(
                    f"Blank image detected: std_dev={normalized_std:.4f}, "
                    f"threshold={self.blank_threshold}"
                )

            return is_blank

        except Exception as e:
            logger.warning(f"Blank check failed: {e}")
            return False

    async def check_frozen(
        self,
        db: AsyncSession,
        camera: Camera,
        num_images: int = 5,
    ) -> bool:
        """
        Check if camera is producing identical (frozen) images.

        Compares hashes of recent images to detect frozen feed.

        Args:
            db: Database session
            camera: Camera to check
            num_images: Number of recent images to compare

        Returns:
            True if images appear frozen
        """
        # Get recent images
        result = await db.execute(
            select(Image)
            .where(Image.camera_id == camera.id)
            .order_by(Image.captured_at.desc())
            .limit(num_images)
        )
        images = result.scalars().all()

        if len(images) < num_images:
            return False

        # Calculate hashes for each image
        hashes = []
        for img_record in images:
            try:
                image_path = f"{settings.output_base_path}/{img_record.file_path}"
                img_hash = self._hash_image(image_path)
                if img_hash:
                    hashes.append(img_hash)
            except Exception as e:
                logger.warning(f"Failed to hash image: {e}")

        if len(hashes) < num_images:
            return False

        # Check if all hashes are identical
        unique_hashes = set(hashes)
        is_frozen = len(unique_hashes) == 1

        if is_frozen:
            logger.warning(f"Camera {camera.name} appears frozen - all recent images identical")

        return is_frozen

    def _hash_image(self, image_path: str) -> Optional[str]:
        """
        Calculate perceptual hash of an image.

        Uses average hash (aHash) for fuzzy matching.

        Args:
            image_path: Path to image file

        Returns:
            Hash string or None if failed
        """
        try:
            with open(image_path, "rb") as f:
                img = PILImage.open(f)

                # Resize to 8x8 for average hash
                small = img.resize((8, 8), PILImage.Resampling.LANCZOS)
                gray = small.convert("L")

                # Calculate average
                pixels = list(gray.getdata())
                avg = sum(pixels) / len(pixels)

                # Build hash
                bits = "".join("1" if p > avg else "0" for p in pixels)

                # Convert to hex
                return hex(int(bits, 2))[2:].zfill(16)

        except Exception as e:
            logger.warning(f"Image hash failed: {e}")
            return None

    async def check_image_data(
        self,
        image_data: bytes,
    ) -> dict:
        """
        Analyze image data for quality issues.

        Args:
            image_data: Raw image bytes

        Returns:
            Dictionary with quality metrics
        """
        try:
            img = PILImage.open(BytesIO(image_data))

            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
                "is_blank": self._is_blank(img),
            }

        except Exception as e:
            logger.warning(f"Image analysis failed: {e}")
            return {
                "error": str(e),
                "is_blank": False,
            }
