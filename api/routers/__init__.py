"""
API Routers Package

FastAPI routers for all API endpoints.
"""

from api.routers.auth import router as auth_router
from api.routers.cameras import router as cameras_router
from api.routers.images import router as images_router
from api.routers.timelapses import router as timelapses_router
from api.routers.multiday import router as multiday_router
from api.routers.health_status import router as health_status_router
from api.routers.notifications import router as notifications_router
from api.routers.settings import router as settings_router
from api.routers.system import router as system_router

__all__ = [
    "auth_router",
    "cameras_router",
    "images_router",
    "timelapses_router",
    "multiday_router",
    "health_status_router",
    "notifications_router",
    "settings_router",
    "system_router",
]
