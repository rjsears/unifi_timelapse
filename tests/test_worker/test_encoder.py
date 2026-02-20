"""
Tests for FFMPEG encoder.
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from worker.ffmpeg.encoder import FFMPEGEncoder


class TestFFMPEGEncoder:
    """Tests for FFMPEGEncoder."""

    @pytest.fixture
    def encoder(self):
        """Create encoder with mocked settings."""
        with patch("worker.ffmpeg.encoder.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(ffmpeg_timeout=3600)
            with patch("worker.ffmpeg.encoder.settings", mock_settings.return_value):
                yield FFMPEGEncoder()

    def test_build_command(self, encoder):
        """Test building FFMPEG command."""
        cmd = encoder._build_command(
            input_file="/tmp/input.txt",
            output_path="/tmp/output.mp4",
            frame_rate=30,
            crf=20,
            pixel_format="yuv444p",
            preset="slow",
        )

        assert "ffmpeg" in cmd
        assert "-y" in cmd
        assert "-f" in cmd
        assert "concat" in cmd
        assert "-c:v" in cmd
        assert "libx264" in cmd
        assert "-preset" in cmd
        assert "slow" in cmd
        assert "-crf" in cmd
        assert "20" in cmd
        assert "-pix_fmt" in cmd
        assert "yuv444p" in cmd

    @pytest.mark.asyncio
    async def test_encode_from_images_no_images(self, encoder):
        """Test encoding fails with no valid images."""
        with pytest.raises(FileNotFoundError, match="No valid image files found"):
            await encoder.encode_from_images(
                image_paths=["/nonexistent/image1.jpg", "/nonexistent/image2.jpg"],
                output_path="/tmp/output.mp4",
            )

    @pytest.mark.asyncio
    async def test_encode_from_images_partial_missing(self, encoder):
        """Test encoding with some missing images."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create one valid image
            img_path = os.path.join(tmpdir, "test.jpg")
            with open(img_path, "wb") as f:
                f.write(b"fake image data")

            output_path = os.path.join(tmpdir, "output.mp4")

            with patch("asyncio.create_subprocess_exec") as mock_exec:
                mock_process = AsyncMock()
                mock_process.returncode = 0
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_exec.return_value = mock_process

                # Create fake output file
                with open(output_path, "wb") as f:
                    f.write(b"fake video data")

                result = await encoder.encode_from_images(
                    image_paths=[img_path, "/nonexistent/image.jpg"],
                    output_path=output_path,
                )

                assert result == Path(output_path)

    @pytest.mark.asyncio
    async def test_encode_from_images_ffmpeg_fails(self, encoder):
        """Test handling of FFMPEG failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = os.path.join(tmpdir, "test.jpg")
            with open(img_path, "wb") as f:
                f.write(b"fake image data")

            output_path = os.path.join(tmpdir, "output.mp4")

            with patch("asyncio.create_subprocess_exec") as mock_exec:
                mock_process = AsyncMock()
                mock_process.returncode = 1
                mock_process.communicate = AsyncMock(return_value=(b"", b"FFMPEG error message"))
                mock_exec.return_value = mock_process

                with pytest.raises(RuntimeError, match="FFMPEG encoding failed"):
                    await encoder.encode_from_images(
                        image_paths=[img_path],
                        output_path=output_path,
                    )

    @pytest.mark.asyncio
    async def test_get_video_info_not_exists(self, encoder):
        """Test getting video info for nonexistent file."""
        result = await encoder.get_video_info("/nonexistent/video.mp4")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_video_info_success(self, encoder):
        """Test getting video info successfully."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"fake video")
            video_path = f.name

        try:
            with patch("asyncio.create_subprocess_exec") as mock_exec:
                mock_process = AsyncMock()
                mock_process.returncode = 0
                mock_process.communicate = AsyncMock(
                    return_value=(b'{"format": {}, "streams": []}', b"")
                )
                mock_exec.return_value = mock_process

                result = await encoder.get_video_info(video_path)

                assert result is not None
                assert "format" in result
        finally:
            os.unlink(video_path)

    @pytest.mark.asyncio
    async def test_get_video_info_ffprobe_fails(self, encoder):
        """Test handling of ffprobe failure."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"fake video")
            video_path = f.name

        try:
            with patch("asyncio.create_subprocess_exec") as mock_exec:
                mock_process = AsyncMock()
                mock_process.returncode = 1
                mock_process.communicate = AsyncMock(return_value=(b"", b"error"))
                mock_exec.return_value = mock_process

                result = await encoder.get_video_info(video_path)
                assert result is None
        finally:
            os.unlink(video_path)

    @pytest.mark.asyncio
    async def test_create_thumbnail_success(self, encoder):
        """Test creating thumbnail successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = os.path.join(tmpdir, "video.mp4")
            with open(video_path, "wb") as f:
                f.write(b"fake video")

            output_path = os.path.join(tmpdir, "thumb.jpg")

            with patch("asyncio.create_subprocess_exec") as mock_exec:
                mock_process = AsyncMock()
                mock_process.returncode = 0
                mock_process.communicate = AsyncMock(return_value=(b"", b""))
                mock_exec.return_value = mock_process

                # Create fake thumbnail
                with open(output_path, "wb") as f:
                    f.write(b"fake thumbnail")

                result = await encoder.create_thumbnail(video_path, output_path)

                assert result is not None
                assert result == Path(output_path)

    @pytest.mark.asyncio
    async def test_create_thumbnail_fails(self, encoder):
        """Test handling thumbnail creation failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = os.path.join(tmpdir, "video.mp4")
            with open(video_path, "wb") as f:
                f.write(b"fake video")

            output_path = os.path.join(tmpdir, "thumb.jpg")

            with patch("asyncio.create_subprocess_exec") as mock_exec:
                mock_process = AsyncMock()
                mock_process.returncode = 1
                mock_process.communicate = AsyncMock(return_value=(b"", b"error"))
                mock_exec.return_value = mock_process

                result = await encoder.create_thumbnail(video_path, output_path)
                assert result is None
