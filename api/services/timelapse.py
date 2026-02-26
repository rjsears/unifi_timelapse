"""
Timelapse Service

Video generation using FFMPEG.
"""

import asyncio
import logging
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.models.camera import Camera
from api.models.image import Image
from api.models.timelapse import Timelapse
from api.services.storage import StorageService

logger = logging.getLogger(__name__)


class TimelapseService:
    """Service for generating timelapse videos."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.storage = StorageService()

    async def generate_daily_timelapse(
        self,
        camera: Camera,
        target_date: date,
        frame_rate: Optional[int] = None,
        crf: Optional[int] = None,
        pixel_format: Optional[str] = None,
    ) -> Timelapse:
        """
        Generate a daily timelapse for a camera.

        Args:
            camera: Camera to generate timelapse for
            target_date: Date to generate timelapse for
            frame_rate: Optional frame rate override
            crf: Optional CRF override
            pixel_format: Optional pixel format override

        Returns:
            Timelapse record
        """
        frame_rate = frame_rate or self.settings.default_frame_rate
        crf = crf or self.settings.default_crf
        pixel_format = pixel_format or self.settings.default_pixel_format

        # Check for existing timelapse
        result = await self.db.execute(
            select(Timelapse).where(
                Timelapse.camera_id == camera.id,
                Timelapse.type == "daily",
                Timelapse.date_start == target_date,
                Timelapse.date_end == target_date,
            )
        )
        timelapse = result.scalar_one_or_none()

        if timelapse is None:
            # Create new timelapse record
            timelapse = Timelapse(
                camera_id=camera.id,
                type="daily",
                date_start=target_date,
                date_end=target_date,
                frame_rate=frame_rate,
                crf=crf,
                pixel_format=pixel_format,
                status="pending",
            )
            self.db.add(timelapse)
            await self.db.commit()
            await self.db.refresh(timelapse)

        # Update status to processing
        timelapse.status = "processing"
        timelapse.started_at = datetime.utcnow()
        await self.db.commit()

        try:
            # Get images for the date
            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt = datetime.combine(target_date, datetime.max.time())

            result = await self.db.execute(
                select(Image)
                .where(
                    Image.camera_id == camera.id,
                    Image.captured_at >= start_dt,
                    Image.captured_at <= end_dt,
                )
                .order_by(Image.captured_at)
            )
            images = result.scalars().all()

            if not images:
                timelapse.status = "failed"
                timelapse.error_message = "No images found for this date"
                await self.db.commit()
                return timelapse

            # Generate video
            output_path = await self._generate_video(
                images=images,
                camera_name=camera.name,
                video_type="daily",
                filename=self.storage.get_daily_video_filename(start_dt),
                frame_rate=frame_rate,
                crf=crf,
                pixel_format=pixel_format,
            )

            # Update timelapse record
            timelapse.file_path = self.storage.get_relative_video_path(
                camera.name,
                "daily",
                self.storage.get_daily_video_filename(start_dt),
            )
            timelapse.file_size = os.path.getsize(output_path)
            timelapse.frame_count = len(images)
            timelapse.duration_seconds = len(images) / frame_rate
            timelapse.status = "completed"
            timelapse.completed_at = datetime.utcnow()

            # Link images to timelapse
            for image in images:
                image.included_in_timelapse_id = timelapse.id

            await self.db.commit()

            logger.info(
                f"Generated daily timelapse for {camera.name} on {target_date}: "
                f"{timelapse.frame_count} frames"
            )

            return timelapse

        except Exception as e:
            timelapse.status = "failed"
            timelapse.error_message = str(e)
            await self.db.commit()
            logger.exception(f"Failed to generate timelapse for {camera.name}")
            raise

    async def _generate_video(
        self,
        images: List[Image],
        camera_name: str,
        video_type: str,
        filename: str,
        frame_rate: int,
        crf: int,
        pixel_format: str,
    ) -> Path:
        """
        Generate video from images using FFMPEG.

        Args:
            images: List of images to include
            camera_name: Camera name
            video_type: Type of video (daily or summary)
            filename: Output filename
            frame_rate: Frame rate
            crf: CRF quality
            pixel_format: Pixel format

        Returns:
            Path to generated video
        """
        # Create output directory
        output_dir = self.storage.get_video_dir(camera_name, video_type)
        output_path = output_dir / filename

        # Create input file list for FFMPEG
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
        ) as f:
            for image in images:
                image_path = f"{self.settings.output_base_path}/{image.file_path}"
                # FFMPEG concat format
                f.write(f"file '{image_path}'\n")
                f.write(f"duration {1 / frame_rate}\n")
            input_file = f.name

        try:
            # Build FFMPEG command
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                input_file,
                "-vf",
                f"fps={frame_rate}",
                "-c:v",
                "libx264",
                "-preset",
                "slow",
                "-crf",
                str(crf),
                "-pix_fmt",
                pixel_format,
                "-movflags",
                "+faststart",
                str(output_path),
            ]

            logger.info(f"Running FFMPEG: {' '.join(cmd)}")

            # Run FFMPEG
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.settings.ffmpeg_timeout,
                )
            except TimeoutError:
                process.kill()
                raise TimeoutError("FFMPEG timed out")

            if process.returncode != 0:
                raise RuntimeError(f"FFMPEG failed: {stderr.decode()}")

            return output_path

        finally:
            # Clean up input file
            os.unlink(input_file)

    async def get_pending_timelapses(self) -> List[Timelapse]:
        """Get all pending timelapse jobs."""
        result = await self.db.execute(select(Timelapse).where(Timelapse.status == "pending"))
        return list(result.scalars().all())
