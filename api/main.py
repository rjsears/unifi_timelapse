"""
FastAPI Main Application

Entry point for the UniFi Timelapse API.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

from api import __version__
from api.auth import hash_password
from api.config import get_settings
from api.database import async_session_maker, close_db, init_db
from api.models.user import User
from api.models.settings import SystemSettings
from api.routers import (
    auth_router,
    cameras_router,
    health_status_router,
    images_router,
    multiday_router,
    notifications_router,
    settings_router,
    system_router,
    timelapses_router,
)

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def create_admin_user() -> None:
    """Create admin user on first startup if it doesn't exist."""
    settings = get_settings()

    async with async_session_maker() as db:
        # Check if admin user exists
        result = await db.execute(select(User).where(User.username == settings.admin_username))
        if result.scalar_one_or_none() is None:
            # Create admin user
            admin = User(
                username=settings.admin_username,
                password_hash=hash_password(settings.admin_password),
                is_active=True,
                is_admin=True,
            )
            db.add(admin)
            await db.commit()
            logger.info(f"Created admin user: {settings.admin_username}")


async def seed_default_settings() -> None:
    """Seed default settings on first startup."""
    settings = get_settings()

    default_settings = [
        (
            "default_capture_interval",
            str(settings.default_capture_interval),
            "integer",
            "capture",
            "Default capture interval in seconds",
        ),
        (
            "default_frame_rate",
            str(settings.default_frame_rate),
            "integer",
            "timelapse",
            "Default video frame rate",
        ),
        (
            "default_crf",
            str(settings.default_crf),
            "integer",
            "timelapse",
            "Default CRF quality (0-51, lower=better)",
        ),
        (
            "default_pixel_format",
            settings.default_pixel_format,
            "string",
            "timelapse",
            "Default pixel format",
        ),
        (
            "ffmpeg_timeout",
            str(settings.ffmpeg_timeout),
            "integer",
            "timelapse",
            "FFMPEG timeout in seconds",
        ),
        (
            "retention_days_images",
            str(settings.retention_days_images),
            "integer",
            "cleanup",
            "Days to retain images",
        ),
        (
            "retention_days_videos",
            str(settings.retention_days_videos),
            "integer",
            "cleanup",
            "Days to retain videos",
        ),
    ]

    async with async_session_maker() as db:
        for key, value, type_, category, description in default_settings:
            result = await db.execute(select(SystemSettings).where(SystemSettings.key == key))
            if result.scalar_one_or_none() is None:
                setting = SystemSettings(
                    key=key,
                    value=value,
                    type=type_,
                    category=category,
                    description=description,
                )
                db.add(setting)

        await db.commit()
        logger.info("Default settings seeded")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info(f"Starting UniFi Timelapse API v{__version__}")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Create admin user
    await create_admin_user()

    # Seed default settings
    await seed_default_settings()

    yield

    # Shutdown
    logger.info("Shutting down UniFi Timelapse API")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="UniFi Timelapse API",
    description="REST API for the UniFi Timelapse System",
    version=__version__,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(cameras_router, prefix="/api")
app.include_router(images_router, prefix="/api")
app.include_router(timelapses_router, prefix="/api")
app.include_router(multiday_router, prefix="/api")
app.include_router(health_status_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(system_router, prefix="/api")


# Root health check (for nginx)
@app.get("/api/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
