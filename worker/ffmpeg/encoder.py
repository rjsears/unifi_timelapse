"""
FFMPEG Encoder

Wrapper for FFMPEG video encoding operations.
"""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import List, Optional

from api.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class FFMPEGEncoder:
    """FFMPEG video encoder for timelapse generation."""

    def __init__(self):
        self.timeout = settings.ffmpeg_timeout

    async def encode_from_images(
        self,
        image_paths: List[str],
        output_path: str,
        frame_rate: int = 30,
        crf: int = 20,
        pixel_format: str = "yuv444p",
        preset: str = "slow",
    ) -> Path:
        """
        Encode a video from a list of images.

        Args:
            image_paths: List of image file paths in order
            output_path: Path for output video file
            frame_rate: Video frame rate
            crf: Constant Rate Factor (quality)
            pixel_format: Pixel format (yuv420p, yuv444p, rgb24)
            preset: Encoding preset (ultrafast to veryslow)

        Returns:
            Path to the generated video

        Raises:
            FileNotFoundError: If no valid images found
            RuntimeError: If FFMPEG fails
            TimeoutError: If encoding times out
        """
        # Verify images exist
        valid_images = [p for p in image_paths if os.path.exists(p)]
        if not valid_images:
            raise FileNotFoundError("No valid image files found")

        if len(valid_images) != len(image_paths):
            logger.warning(
                f"Only {len(valid_images)}/{len(image_paths)} images found"
            )

        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create input file list for FFMPEG concat demuxer
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
        ) as f:
            for image_path in valid_images:
                # FFMPEG concat format requires escaping single quotes
                escaped_path = image_path.replace("'", "'\\''")
                f.write(f"file '{escaped_path}'\n")
                f.write(f"duration {1/frame_rate}\n")
            # Repeat last frame to ensure it's included
            if valid_images:
                escaped_path = valid_images[-1].replace("'", "'\\''")
                f.write(f"file '{escaped_path}'\n")
            input_file = f.name

        try:
            # Build FFMPEG command
            cmd = self._build_command(
                input_file=input_file,
                output_path=output_path,
                frame_rate=frame_rate,
                crf=crf,
                pixel_format=pixel_format,
                preset=preset,
            )

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
                    timeout=self.timeout,
                )
            except TimeoutError:
                process.kill()
                await process.wait()
                raise TimeoutError(
                    f"FFMPEG encoding timed out after {self.timeout}s"
                )

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"FFMPEG failed: {error_msg}")
                raise RuntimeError(f"FFMPEG encoding failed: {error_msg}")

            # Verify output
            output = Path(output_path)
            if not output.exists():
                raise RuntimeError("FFMPEG did not create output file")

            logger.info(
                f"Video encoded successfully: {output_path} "
                f"({output.stat().st_size / 1024 / 1024:.2f} MB)"
            )

            return output

        finally:
            # Clean up input file
            try:
                os.unlink(input_file)
            except Exception:
                pass

    def _build_command(
        self,
        input_file: str,
        output_path: str,
        frame_rate: int,
        crf: int,
        pixel_format: str,
        preset: str,
    ) -> List[str]:
        """
        Build the FFMPEG command.

        Args:
            input_file: Path to concat input file
            output_path: Output video path
            frame_rate: Frame rate
            crf: Quality factor
            pixel_format: Pixel format
            preset: Encoding preset

        Returns:
            List of command arguments
        """
        return [
            "ffmpeg",
            "-y",  # Overwrite output
            "-f", "concat",  # Concat demuxer
            "-safe", "0",  # Allow absolute paths
            "-i", input_file,  # Input file list
            "-vf", f"fps={frame_rate}",  # Output frame rate
            "-c:v", "libx264",  # H.264 codec
            "-preset", preset,  # Encoding preset
            "-crf", str(crf),  # Quality
            "-pix_fmt", pixel_format,  # Pixel format
            "-movflags", "+faststart",  # Web optimization
            output_path,
        ]

    async def get_video_info(self, video_path: str) -> Optional[dict]:
        """
        Get information about a video file using ffprobe.

        Args:
            video_path: Path to video file

        Returns:
            Dictionary with video info or None if failed
        """
        if not os.path.exists(video_path):
            return None

        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path,
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=30,
            )

            if process.returncode != 0:
                return None

            import json
            return json.loads(stdout.decode())

        except Exception as e:
            logger.warning(f"Failed to get video info: {e}")
            return None

    async def create_thumbnail(
        self,
        video_path: str,
        output_path: str,
        timestamp: str = "00:00:01",
    ) -> Optional[Path]:
        """
        Create a thumbnail from a video.

        Args:
            video_path: Path to video file
            output_path: Path for thumbnail output
            timestamp: Time position for thumbnail

        Returns:
            Path to thumbnail or None if failed
        """
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-ss", timestamp,
            "-vframes", "1",
            "-q:v", "2",
            output_path,
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            await asyncio.wait_for(process.communicate(), timeout=30)

            if process.returncode == 0 and os.path.exists(output_path):
                return Path(output_path)
            return None

        except Exception as e:
            logger.warning(f"Failed to create thumbnail: {e}")
            return None
