"""
Tests for image quality checker.
"""

import pytest
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from health.checks.image_quality import ImageQualityChecker


class TestImageQualityChecker:
    """Tests for ImageQualityChecker."""

    @pytest.fixture
    def checker(self):
        """Create image quality checker."""
        with patch("health.checks.image_quality.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                blank_threshold=0.05,
                output_base_path="/tmp/test_output",
            )
            with patch("health.checks.image_quality.settings", mock_settings.return_value):
                yield ImageQualityChecker()

    @pytest.fixture
    def mock_camera(self):
        """Create mock camera."""
        camera = MagicMock()
        camera.id = uuid4()
        camera.name = "Test Camera"
        return camera

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    def test_is_blank_dark_image(self, checker):
        """Test detecting a dark/blank image."""
        # Create a tiny dark image
        from PIL import Image

        img = Image.new("RGB", (10, 10), color=(0, 0, 0))

        result = checker._is_blank(img)

        assert result is True

    def test_is_blank_normal_image(self, checker):
        """Test normal image is not detected as blank."""
        from PIL import Image

        # Create an image with varied colors
        img = Image.new("RGB", (10, 10), color=(128, 128, 128))
        pixels = img.load()
        for i in range(10):
            for j in range(10):
                # Create some variance
                pixels[i, j] = ((i * 25) % 256, (j * 25) % 256, 128)

        result = checker._is_blank(img)

        assert result is False

    def test_is_blank_exception(self, checker):
        """Test handling exceptions in blank check."""
        mock_img = MagicMock()
        mock_img.convert.side_effect = Exception("Conversion error")

        result = checker._is_blank(mock_img)

        assert result is False

    @pytest.mark.asyncio
    async def test_check_blank_no_images(self, checker, mock_db, mock_camera):
        """Test blank check when no images exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await checker.check_blank(mock_db, mock_camera)

        assert result is False

    @pytest.mark.asyncio
    async def test_check_blank_file_error(self, checker, mock_db, mock_camera):
        """Test blank check when file can't be opened."""
        mock_image = MagicMock()
        mock_image.file_path = "nonexistent/image.jpg"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_image
        mock_db.execute.return_value = mock_result

        result = await checker.check_blank(mock_db, mock_camera)

        assert result is False

    def test_hash_image_nonexistent(self, checker):
        """Test hashing nonexistent image."""
        result = checker._hash_image("/nonexistent/image.jpg")

        assert result is None

    @pytest.mark.asyncio
    async def test_check_frozen_not_enough_images(self, checker, mock_db, mock_camera):
        """Test frozen check when not enough images."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [MagicMock(), MagicMock()]
        mock_db.execute.return_value = mock_result

        result = await checker.check_frozen(mock_db, mock_camera, num_images=5)

        assert result is False

    @pytest.mark.asyncio
    async def test_check_image_data_valid(self, checker):
        """Test analyzing valid image data."""
        from PIL import Image
        import io

        # Create a test image
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        image_data = buffer.getvalue()

        result = await checker.check_image_data(image_data)

        assert "width" in result
        assert "height" in result
        assert result["width"] == 100
        assert result["height"] == 100
        assert "is_blank" in result

    @pytest.mark.asyncio
    async def test_check_image_data_invalid(self, checker):
        """Test analyzing invalid image data."""
        result = await checker.check_image_data(b"not an image")

        assert "error" in result
        assert result["is_blank"] is False
