"""
ORCA — ORCA Chat Router (Phase 0 Stub)
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
    """
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages"))
    
    from orca_core.supervisor import orca_supervisor
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    
    try:
        session_id = request.session_id or uuid.uuid4()
        
        # Check if session exists to retrieve history (stubbed for simplicity)
        from sqlalchemy import select
        result = await db.execute(select(ORCASessionORM).where(ORCASessionORM.id == session_id))
        session = result.scalar_one_or_none()
        
        historical_messages = []
        if session and session.messages:
            for msg in session.messages:
                if msg["role"] == "user":
                    historical_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    historical_messages.append(SystemMessage(content=msg["content"]))
        
        if historical_messages:
            from langchain_core.messages import AIMessage
            historical_messages = [AIMessage(content=m.content) if isinstance(m, SystemMessage) else m for m in historical_messages]
        
        messages = historical_messages + [HumanMessage(content=request.message)]
        
        # Run LangGraph supervisor
        initial_state = {
            "messages": messages,
            "session_id": str(session_id),
            "incident_id": str(request.incident_id) if request.incident_id else None,
            "user_query": request.message,
            "current_location": None,
            "current_time": datetime.utcnow().isoformat(),
            "current_intent": None,
            "detected_language": request.language_hint or "en",
            "response_language": request.language_hint or "en",
            "selected_agents": [],
            "evidence": [],
            "plan": [],
            "reasoning_metadata": {},
            "final_answer": None,
            "confidence": 1.0,
            "status": "in_progress",
            "error": None
        }
        
        final_state = await orca_supervisor.ainvoke(initial_state)
            
        final_messages = final_state.get("messages", [])
        
        # Extract from final state
        response_msg = final_state.get("final_answer")
        if not response_msg:
            # Fallback if the tool wasn't called
            response_msg = final_messages[-1].content if final_messages else "No response generated."
            
        detected_lang = final_state.get("detected_language", request.language_hint or "en")
        evidence_dicts = final_state.get("evidence", [])
        plan = final_state.get("plan", [])
        
        # Convert evidence dictionaries to EvidenceItem models
        evidence = [EvidenceItem(**e) for e in evidence_dicts]

        # Persist session
        session_messages = []
        if session and session.messages:
            session_messages = list(session.messages)
            
        session_messages.extend([
            {"role": "user", "content": request.message, "created_at": datetime.utcnow().isoformat()},
            {"role": "assistant", "content": response_msg, "created_at": datetime.utcnow().isoformat()},
        ])
        
        if not session:
            session_orm = ORCASessionORM(
                id=session_id,
                incident_id=request.incident_id,
                user_query=request.message,
                detected_language=detected_lang,
                messages=session_messages,
                evidence=[e.model_dump() for e in evidence],
                status=SessionStatus.DONE,
            )
            db.add(session_orm)
        else:
            session.messages = session_messages
            session.evidence = [e.model_dump() for e in evidence]
            session.detected_language = detected_lang
            db.add(session)
            
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(session, "messages")
            flag_modified(session, "evidence")
            
        await db.flush()

        lang_name = SUPPORTED_LANGUAGES.get(detected_lang, "English")

        return ORCAResponse(
            session_id=session_id,
            message=response_msg,
            detected_language=detected_lang,
            evidence=evidence,
            plan=plan,
            suggestions=[],
            incident_id=request.incident_id,
            visualization=final_state.get("visualization"),
            report=final_state.get("report")
        )
    except Exception as e:
        import traceback
        import logging
        from fastapi import HTTPException
        err_msg = traceback.format_exc()
        logging.error(f"ORCA LLM Error: {err_msg}")
        
        # ALL LLM/provider failures (503, 404, timeout, connection reset,
        # httpx.ReadTimeout, invalid model, 429, etc.) are surfaced as
        # HTTP 503 to the frontend so it can cleanly reset UI state.
        raise HTTPException(
            status_code=503,
            detail="ORCA is temporarily unavailable because the AI service is unavailable. Please try again."
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
