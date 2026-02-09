"""
Capture Service

Camera image capture operations.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo
from io import BytesIO
from typing import List, Optional

import httpx
from PIL import Image as PILImage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.models.camera import Camera
from api.models.image import Image
from api.services.storage import StorageService

logger = logging.getLogger(__name__)


@dataclass
class CaptureResult:
    """Result of a capture attempt."""

    camera: Camera
    success: bool
    timestamp: datetime
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    error: Optional[str] = None


class CaptureService:
    """Service for capturing images from cameras."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.storage = StorageService()

    def _get_local_time(self) -> datetime:
        """Get current time in configured timezone as naive datetime."""
        tz = ZoneInfo(self.settings.tz)
        return datetime.now(tz).replace(tzinfo=None)

    async def capture_single(
        self,
        camera: Camera,
        client: httpx.AsyncClient,
    ) -> CaptureResult:
        """
        Capture a single image from a camera.

        Args:
            camera: Camera to capture from
            client: HTTP client

        Returns:
            CaptureResult with success/failure info
        """
        timestamp = self._get_local_time()

        # Check blackout period
        if camera.is_in_blackout():
            return CaptureResult(
                camera=camera,
                success=False,
                timestamp=timestamp,
                error="Camera is in blackout period",
            )

        try:
            # Fetch image
            response = await client.get(
                camera.url,
                timeout=self.settings.capture_timeout,
            )
            response.raise_for_status()

            image_data = response.content

            # Get image dimensions
            width, height = None, None
            try:
                img = PILImage.open(BytesIO(image_data))
                width, height = img.size
            except Exception:
                pass

            # Save image
            file_path, file_size = self.storage.save_image(
                camera.name,
                timestamp,
                image_data,
            )

            # Get relative path for database
            relative_path = self.storage.get_relative_image_path(
                camera.name,
                timestamp,
            )

            # Create database record
            image = Image(
                camera_id=camera.id,
                captured_at=timestamp,
                file_path=relative_path,
                file_size=file_size,
                width=width,
                height=height,
            )
            self.db.add(image)

            # Update camera status
            camera.last_capture_at = timestamp
            camera.last_capture_status = "success"
            camera.consecutive_errors = 0

            await self.db.commit()

            logger.info(f"Captured image from {camera.name}: {relative_path}")

            return CaptureResult(
                camera=camera,
                success=True,
                timestamp=timestamp,
                file_path=relative_path,
                file_size=file_size,
                width=width,
                height=height,
            )

        except httpx.TimeoutException:
            error = "Connection timeout"
            logger.warning(f"Timeout capturing from {camera.name}")
        except httpx.HTTPStatusError as e:
            error = f"HTTP error: {e.response.status_code}"
            logger.warning(f"HTTP error capturing from {camera.name}: {error}")
        except Exception as e:
            error = str(e)
            logger.exception(f"Error capturing from {camera.name}")

        # Update camera error status
        camera.last_capture_at = timestamp
        camera.last_capture_status = "failed"
        camera.consecutive_errors += 1
        await self.db.commit()

        return CaptureResult(
            camera=camera,
            success=False,
            timestamp=timestamp,
            error=error,
        )

    async def capture_all(
        self,
        cameras: Optional[List[Camera]] = None,
    ) -> List[CaptureResult]:
        """
        Capture images from all active cameras concurrently.

        Args:
            cameras: Optional list of cameras. If None, fetch all active cameras.

        Returns:
            List of CaptureResults
        """
        if cameras is None:
            result = await self.db.execute(
                select(Camera).where(Camera.is_active == True)
            )
            cameras = list(result.scalars().all())

        if not cameras:
            return []

        # Create semaphore to limit concurrent captures
        semaphore = asyncio.Semaphore(self.settings.max_concurrent_captures)

        async def capture_with_semaphore(
            camera: Camera,
            client: httpx.AsyncClient,
        ) -> CaptureResult:
            async with semaphore:
                return await self.capture_single(camera, client)

        # Capture all images concurrently
        async with httpx.AsyncClient() as client:
            tasks = [
                capture_with_semaphore(camera, client)
                for camera in cameras
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.exception(f"Exception capturing from camera: {result}")
                processed_results.append(
                    CaptureResult(
                        camera=cameras[i],
                        success=False,
                        timestamp=self._get_local_time(),
                        error=str(result),
                    )
                )
            else:
                processed_results.append(result)

        return processed_results

    async def get_cameras_due_for_capture(self) -> List[Camera]:
        """
        Get cameras that are due for capture based on their interval.

        Returns:
            List of cameras due for capture
        """
        now = self._get_local_time()

        result = await self.db.execute(
            select(Camera).where(Camera.is_active == True)
        )
        cameras = result.scalars().all()

        due_cameras = []
        for camera in cameras:
            # Skip if in blackout
            if camera.is_in_blackout():
                continue

            # Check if enough time has passed since last capture
            if camera.last_capture_at is None:
                due_cameras.append(camera)
            else:
                # Strip timezone info for comparison (DB may return tz-aware)
                last_capture = camera.last_capture_at
                if last_capture.tzinfo is not None:
                    last_capture = last_capture.replace(tzinfo=None)
                elapsed = (now - last_capture).total_seconds()
                if elapsed >= camera.capture_interval:
                    due_cameras.append(camera)

        return due_cameras
