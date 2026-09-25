"""
SAMUDRA-AI / ORCA — ORCA Chat Router (Phase 0 Stub)
POST /api/v1/orca/chat
GET  /api/v1/orca/session/{session_id}

Phase 0: Returns a stub response acknowledging the query.
Phase 1: Will be replaced with full LangGraph ORCA supervisor.
"""

from __future__ import annotations

import uuid
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "shared-types"))

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    ORCAQueryRequest,
    ORCAResponse,
    ORCASession,
    EvidenceItem,
    ChatMessage,
    MessageRole,
    SessionStatus,
)
from core.database import get_db
from core.db_models import ORCASessionORM
from core.settings import settings

router = APIRouter(prefix="/api/v1/orca", tags=["orca"])


SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi (हिंदी)",
    "ta": "Tamil (தமிழ்)",
    "ml": "Malayalam (മലയാളം)",
    "te": "Telugu (తెలుగు)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "mr": "Marathi (मराठी)",
    "gu": "Gujarati (ગુજરાતી)",
    "bn": "Bengali (বাংলা)",
    "or": "Odia (ଓଡ଼ିଆ)",
}


@router.post("/chat", response_model=ORCAResponse, summary="Query ORCA — Marine Intelligence Brain")
async def orca_chat(
    request: ORCAQueryRequest,
    db: AsyncSession = Depends(get_db),
) -> ORCAResponse:
    """
    Send a natural language query to ORCA.

    ORCA understands English and Indian regional languages.
    Maintains multi-turn conversation context via session_id.

    **Phase 0 stub** — returns a structured placeholder response.
    Full LangGraph agent workflow implemented in Phase 1.
    """
    session_id = request.session_id or uuid.uuid4()

    # Phase 0 stub evidence
    evidence = [
        EvidenceItem(
            source="STUB",
            agent="ORCA-Supervisor",
            tool="phase_0_stub",
            summary=(
                "Phase 0 stub response. Full ORCA agent orchestration "
                "will be implemented in Phase 1."
            ),
            is_simulated=True,
            confidence=None,
        )
    ]

    # Persist session
    session_orm = ORCASessionORM(
        id=session_id,
        incident_id=request.incident_id,
        user_query=request.message,
        detected_language=request.language_hint or "en",
        messages=[
            {"role": "user", "content": request.message, "created_at": datetime.utcnow().isoformat()},
        ],
        evidence=[e.model_dump() for e in evidence],
        status=SessionStatus.DONE,
    )
    db.add(session_orm)
    await db.flush()

    demo_note = " [DEMO MODE — ORCA Phase 0 Scaffold]" if settings.enable_demo_mode else ""
    lang_name = SUPPORTED_LANGUAGES.get(request.language_hint or "en", "English")

    return ORCAResponse(
        session_id=session_id,
        message=(
            f"Namaste! I am ORCA — your Marine Intelligence Brain.{demo_note}\n\n"
            f"I received your query: \"{request.message}\"\n\n"
            f"Language: {lang_name} | Incident: {request.incident_id or 'None'}\n\n"
            f"🚧 Full ORCA agent orchestration (LangGraph + specialized agents) "
            f"will be operational in Phase 1. The platform backbone is now live:\n"
            f"  ✅ PostgreSQL + PostGIS database\n"
            f"  ✅ Redis cache\n"
            f"  ✅ Shared data models\n"
            f"  ✅ API scaffold\n"
            f"  ✅ Session storage\n"
            f"  🔜 LangGraph ORCA supervisor (Phase 1)\n"
            f"  🔜 Specialized marine agents (Phase 2)\n"
            f"  🔜 RK4 drift simulation (Phase 9)"
        ),
        detected_language=request.language_hint or "en",
        evidence=evidence,
        plan=[
            {"step": 1, "agent": "ORCA-Supervisor", "action": "parse_intent", "status": "stub"},
            {"step": 2, "agent": "HydroMeteo", "action": "fetch_weather", "status": "pending"},
            {"step": 3, "agent": "SARPhysics", "action": "rk4_drift", "status": "pending"},
        ],
        suggestions=[
            "What is the current sea condition at 12.5°N, 80.2°E?",
            "Is vessel MH-1234 in a restricted zone?",
            "Run drift prediction for SOS at 13.1°N, 74.8°E",
            "Show PFZ advisory for Tamil Nadu coast today",
        ],
        incident_id=request.incident_id,
    )


@router.get("/session/{session_id}", response_model=ORCASession, summary="Get ORCA session")
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ORCASession:
    from sqlalchemy import select
    from fastapi import HTTPException, status as http_status

    result = await db.execute(
        select(ORCASessionORM).where(ORCASessionORM.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="ORCA session not found",
        )

    return ORCASession(
        id=session.id,
        incident_id=session.incident_id,
        user_query=session.user_query,
        detected_language=session.detected_language,
        messages=[ChatMessage(**m) for m in (session.messages or [])],
        evidence=[EvidenceItem(**e) for e in (session.evidence or [])],
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )
