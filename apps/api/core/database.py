"""
ORCA — Async Database Engine & Session Factory
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.sql import text

from .settings import settings

connect_args = {}
if "asyncpg" in settings.database_url:
    connect_args["server_settings"] = {"search_path": "public,extensions"}
elif "psycopg" in settings.database_url:
    connect_args["options"] = "-c search_path=public,extensions"

# Create the async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.is_development,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args=connect_args,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_db_health() -> bool:
    """Check database connectivity and PostGIS availability."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT PostGIS_Full_Version()"))
            result.scalar()
            return True
    except Exception:
        # Try plain connectivity without PostGIS check
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception:
            return False
