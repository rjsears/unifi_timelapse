"""
Tests for capture service.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from api.models.camera import Camera
from api.services.capture import CaptureService, CaptureResult


@pytest.fixture
def mock_camera() -> Camera:
    """Create a mock camera."""
    camera = Camera(
        id=uuid4(),
        name="Test Camera",
        url="http://192.168.1.100/snap.jpeg",
        is_active=True,
        capture_interval=60,
    )
    return camera


@pytest.mark.asyncio
async def test_capture_service_init(db_session: AsyncSession):
    """Test CaptureService initialization."""
    service = CaptureService(db_session)
    assert service.db == db_session
    assert service.settings is not None
    assert service.storage is not None


@pytest.mark.asyncio
async def test_get_local_time(db_session: AsyncSession):
    """Test getting local time."""
    service = CaptureService(db_session)
    local_time = service._get_local_time()
    assert isinstance(local_time, datetime)
    assert local_time.tzinfo is None  # Should be naive


@pytest.mark.asyncio
async def test_capture_result_dataclass():
    """Test CaptureResult dataclass."""
    camera = MagicMock()
    result = CaptureResult(
        camera=camera,
        success=True,
        timestamp=datetime.now(),
        file_path="/path/to/image.jpg",
        file_size=1024,
    )
    assert result.success is True
    assert result.file_path == "/path/to/image.jpg"
    assert result.file_size == 1024
    assert result.error is None


@pytest.mark.asyncio
async def test_capture_single_blackout(db_session: AsyncSession, mock_camera: Camera):
    """Test capture during blackout period returns early."""
    service = CaptureService(db_session)

    # Mock camera to be in blackout
    with patch.object(mock_camera, 'is_in_blackout', return_value=True):
        mock_client = AsyncMock()
        result = await service.capture_single(mock_camera, mock_client)

    assert result.success is False
    assert "blackout" in result.error.lower()


@pytest.mark.asyncio
async def test_get_cameras_due_for_capture_empty(db_session: AsyncSession):
    """Test getting cameras due when none are active."""
    service = CaptureService(db_session)
    cameras = await service.get_cameras_due_for_capture()
    assert cameras == []


@pytest.mark.asyncio
async def test_get_cameras_due_for_capture_never_captured(db_session: AsyncSession):
    """Test cameras that have never captured are due."""
    # Add camera without last_capture_at
    camera = Camera(
        id=uuid4(),
        name="New Camera",
        url="http://192.168.1.100/snap.jpeg",
        is_active=True,
        capture_interval=60,
        last_capture_at=None,
    )
    db_session.add(camera)
    await db_session.commit()

    service = CaptureService(db_session)
    cameras = await service.get_cameras_due_for_capture()

    assert len(cameras) == 1
    assert cameras[0].name == "New Camera"
