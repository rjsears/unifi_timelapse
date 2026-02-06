"""
FastAPI Dependencies

Shared dependencies for the API.
"""

from typing import AsyncGenerator

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.database import async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency.

    Provides an async database session that is automatically
    closed when the request is complete.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """
    Redis connection dependency.

    Provides a Redis connection that is automatically
    closed when the request is complete.
    """
    settings = get_settings()
    r = redis.from_url(settings.redis_url)
    try:
        yield r
    finally:
        await r.close()
