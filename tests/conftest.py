"""
Test Configuration and Fixtures

Shared fixtures for all tests.
"""

import asyncio
import os
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Set test environment variables before importing app modules
# Only set defaults if not already set (CI provides these)
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test_user:test_password@localhost:5432/timelapse_test"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("FIRST_SUPERUSER_EMAIL", "admin@test.com")
os.environ.setdefault("FIRST_SUPERUSER_PASSWORD", "testpassword123")
os.environ.setdefault("OUTPUT_BASE_PATH", "/tmp/test_output")
os.environ.setdefault("TZ", "America/Chicago")

from datetime import date, datetime, time, timedelta

from api.database import Base
from api.main import app
from api.models.user import User
from api.models.camera import Camera
from api.models.image import Image
from api.models.timelapse import Timelapse
from api.models.notification_config import NotificationConfig
from api.models.multiday_config import MultidayConfig
from api.models.settings import SystemSettings
from api.models.camera_health import CameraHealth
from api.auth import hash_password


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create async database engine for testing."""
    database_url = os.environ.get("DATABASE_URL")
    engine = create_async_engine(
        database_url,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for testing."""
    async_session = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    from api.database import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=uuid4(),
        username="testuser@test.com",
        password_hash=hash_password("testpassword123"),
        is_active=True,
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user."""
    user = User(
        id=uuid4(),
        username="admin@test.com",
        password_hash=hash_password("adminpassword123"),
        is_active=True,
        is_admin=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """Get authentication headers for test user."""
    response = await client.post(
        "/api/auth/login",
        json={
            "username": "testuser@test.com",
            "password": "testpassword123",
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
async def admin_headers(client: AsyncClient, admin_user: User) -> dict:
    """Get authentication headers for admin user."""
    response = await client.post(
        "/api/auth/login",
        json={
            "username": "admin@test.com",
            "password": "adminpassword123",
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ═══════════════════════════════════════════
# Additional Fixtures for Coverage Tests
# ═══════════════════════════════════════════


@pytest_asyncio.fixture(scope="function")
async def sample_camera(db_session: AsyncSession) -> Camera:
    """Create a sample camera for testing."""
    camera = Camera(
        id=uuid4(),
        name="Test Camera 1",
        ip_address="192.168.1.100",
        is_active=True,
        capture_interval=60,
    )
    db_session.add(camera)
    await db_session.commit()
    await db_session.refresh(camera)
    return camera


@pytest_asyncio.fixture(scope="function")
async def sample_images(db_session: AsyncSession, sample_camera: Camera) -> list:
    """Create sample images for a camera."""
    images = []
    base_time = datetime.now() - timedelta(hours=24)
    for i in range(10):
        image = Image(
            id=uuid4(),
            camera_id=sample_camera.id,
            captured_at=base_time + timedelta(hours=i),
            file_path=f"cameras/{sample_camera.name}/2026/02/19/image_{i:04d}.jpg",
            file_size=1024 * (i + 1),
            width=1920,
            height=1080,
            is_protected=False,
        )
        images.append(image)
        db_session.add(image)
    await db_session.commit()
    for img in images:
        await db_session.refresh(img)
    return images


@pytest_asyncio.fixture(scope="function")
async def sample_timelapse(db_session: AsyncSession, sample_camera: Camera) -> Timelapse:
    """Create a sample timelapse for testing."""
    timelapse = Timelapse(
        id=uuid4(),
        camera_id=sample_camera.id,
        type="daily",
        date_start=date.today() - timedelta(days=1),
        date_end=date.today() - timedelta(days=1),
        file_path=f"cameras/{sample_camera.name}/videos/timelapse_20260218.mp4",
        file_size=1024 * 1024 * 10,
        frame_count=2880,
        frame_rate=30,
        crf=20,
        pixel_format="yuv444p",
        duration_seconds=96.0,
        status="completed",
        completed_at=datetime.now(),
    )
    db_session.add(timelapse)
    await db_session.commit()
    await db_session.refresh(timelapse)
    return timelapse


@pytest_asyncio.fixture(scope="function")
async def notification_config(db_session: AsyncSession) -> NotificationConfig:
    """Create a notification config for testing."""
    config = NotificationConfig(
        id=uuid4(),
        name="Test Notifications",
        apprise_url="json://localhost:8080/notify",
        is_enabled=True,
        notify_on_capture_fail=True,
        notify_on_timelapse_done=True,
        notify_on_storage_warn=True,
        notify_on_camera_down=True,
        min_failures_before_alert=3,
    )
    db_session.add(config)
    await db_session.commit()
    await db_session.refresh(config)
    return config


@pytest_asyncio.fixture(scope="function")
async def multiday_config(db_session: AsyncSession, sample_camera: Camera) -> MultidayConfig:
    """Create a multiday config for testing."""
    config = MultidayConfig(
        id=uuid4(),
        camera_id=sample_camera.id,
        name="Weekly Summary",
        is_enabled=True,
        mode="historical",
        status="idle",
        images_per_hour=2,
        days_to_include=7,
        generation_day="sunday",
        generation_time=time(2, 0, 0),
        frame_rate=30,
        crf=20,
        pixel_format="yuv444p",
    )
    db_session.add(config)
    await db_session.commit()
    await db_session.refresh(config)
    return config


@pytest_asyncio.fixture(scope="function")
async def sample_settings(db_session: AsyncSession) -> list:
    """Create sample settings for testing."""
    settings = [
        SystemSettings(
            id=uuid4(),
            key="image_retention_days",
            value="30",
            type="integer",
            category="cleanup",
            description="Days to retain images",
        ),
        SystemSettings(
            id=uuid4(),
            key="video_retention_days",
            value="90",
            type="integer",
            category="cleanup",
            description="Days to retain videos",
        ),
        SystemSettings(
            id=uuid4(),
            key="storage_warning_threshold",
            value="85",
            type="integer",
            category="storage",
            description="Storage warning percentage",
        ),
    ]
    for setting in settings:
        db_session.add(setting)
    await db_session.commit()
    for setting in settings:
        await db_session.refresh(setting)
    return settings


@pytest_asyncio.fixture(scope="function")
async def camera_health_records(db_session: AsyncSession, sample_camera: Camera) -> list:
    """Create camera health records for testing."""
    from datetime import timezone

    records = []
    # Use timezone-aware datetime for consistency with the router
    base_time = datetime.now(timezone.utc) - timedelta(hours=24)
    for i in range(24):
        record = CameraHealth(
            id=uuid4(),
            camera_id=sample_camera.id,
            checked_at=base_time + timedelta(hours=i),
            is_reachable=i != 5,  # One offline period
            response_time_ms=50 + (i * 2) if i != 5 else None,
            is_image_blank=False,
            is_image_frozen=False,
            error_message="Connection timeout" if i == 5 else None,
        )
        records.append(record)
        db_session.add(record)
    await db_session.commit()
    for rec in records:
        await db_session.refresh(rec)
    return records
