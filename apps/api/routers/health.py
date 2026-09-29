"""
ORCA — Health Check Router
GET /api/v1/health
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "shared-types"))

from fastapi import APIRouter
from models import HealthStatus
from core.database import check_db_health
from core.settings import settings
import redis.asyncio as aioredis

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health", response_model=HealthStatus, summary="Platform health check")
async def health_check() -> HealthStatus:
    """
    Returns the health status of the ORCA platform.
    Checks database (PostgreSQL + PostGIS) and Redis connectivity.
    """
    db_ok = await check_db_health()

    # Check Redis
    redis_ok = False
    try:
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        redis_ok = True
    except Exception:
        pass

    return HealthStatus(
        status="ok" if (db_ok and redis_ok) else "degraded",
        db="ok" if db_ok else "error",
        redis="ok" if redis_ok else "error",
        version=settings.version,
        phase="Phase 0 — Repository Scaffold",
    )
