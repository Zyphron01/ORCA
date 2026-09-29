"""
ORCA — FastAPI Application Entry Point
====================================================
Agentic AI Marine Intelligence Platform
Team Bytecrats | SIH 2026 | PS ID: SIH26176
"""

from __future__ import annotations

import sys
import os

# Make shared packages importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "packages", "shared-types"))

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.settings import settings
from core.database import engine
from core.db_models import Base
from core.logging import configure_logging, get_logger
from routers.health import router as health_router
from routers.vessels import router as vessels_router
from routers.incidents import router as incidents_router
from routers.orca import router as orca_router
from routers.sos import router as sos_router

configure_logging()
log = get_logger("ORCA.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup / shutdown lifecycle."""
    log.info(
        "ORCA starting",
        version=settings.version,
        env=settings.app_env,
        demo_mode=settings.enable_demo_mode,
        phase="Phase 0 - Repository Scaffold",
    )

    # Create database tables (Alembic handles production migrations)
    # Graceful startup: warn if DB unavailable, don't crash
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        log.info("Database tables created/verified")
    except Exception as exc:
        log.warning(
            "Database not available at startup - running in degraded mode",
            error=str(exc),
            hint="Start PostgreSQL with: docker compose -f infra/docker-compose.yml up -d",
        )

    yield

    log.info("ORCA shutting down")
    await engine.dispose()


# ============================================================
# FastAPI App Instance
# ============================================================

app = FastAPI(
    title="ORCA Marine Intelligence Platform",
    description="""
## ORCA — Ocean Reasoning and Collaborative Agents

**ORCA** is an Agentic AI Marine Intelligence Platform for Indian fishermen
and the Indian Coast Guard.

**ORCA** is the central Marine Intelligence Brain that:
- Understands natural language (English + Indian regional languages)
- Plans multi-step marine intelligence tasks
- Delegates to specialized agents (Hydro-Meteo, Marine EO, Hazard Sentry, SAR Physics)
- Synthesizes evidence into actionable rescue plans and safety alerts
- Produces drift predictions, live maps, and structured intelligence reports

### Data Sources (via mock adapters — clearly labelled)
- INCOIS THREDDS: Ocean currents, wave heights, SARAT
- IMD Mausam: Coastal wind advisories
- Bhoonidhi: Oceansat-3 chlorophyll, INSAT-3D SST
- ISRO Transponders: DAT-SG / Nabhmitra (BLE bridge)

### Current Phase
**Phase 0** — Repository scaffold, shared types, database, API skeleton

---
*Team Bytecrats | SIH 2026 | Problem Statement ID: SIH26176*
    """,
    version=settings.version,
    contact={
        "name": "Team Bytecrats",
        "url": "https://github.com/ORCA",
    },
    license_info={
        "name": "SIH 2026 — Educational Use",
    },
    lifespan=lifespan,
)

# ============================================================
# Middleware
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    log.info(
        "request",
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else "unknown",
    )
    response = await call_next(request)
    log.info("response", status_code=response.status_code, path=request.url.path)
    return response


# ============================================================
# Exception Handlers
# ============================================================


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "type": "validation_error"},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.error("unhandled_exception", error=str(exc), path=request.url.path, exc_info=True)
    import traceback
    with open("global_traceback.txt", "w", encoding="utf-8") as f:
        f.write(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": "internal_error",
            "path": str(request.url.path),
        },
    )


# ============================================================
# Routers
# ============================================================

from routers.route import router as route_router
from routers.marine import router as marine_router
from routers.reports import router as reports_router

app.include_router(health_router)
app.include_router(vessels_router)
app.include_router(incidents_router)
app.include_router(orca_router)
app.include_router(sos_router)
app.include_router(route_router)
app.include_router(marine_router)
app.include_router(reports_router)


# ============================================================
# Root redirect
# ============================================================


@app.get("/", include_in_schema=False)
async def root():
    return {
        "platform": "ORCA Marine Intelligence Platform",
        "version": settings.version,
        "phase": "Phase 0 — Repository Scaffold",
        "team": "Bytecrats",
        "sih": "SIH 2026 | PS ID: SIH26176",
        "docs": "/docs",
        "health": "/api/v1/health",
        "demo_mode": settings.enable_demo_mode,
        "status": "operational",
    }
