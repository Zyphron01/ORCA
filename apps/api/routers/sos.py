import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from core.database import get_db
from core.db_models import IncidentORM, VesselORM, DriftPredictionORM
from models import IncidentStatus, IncidentType, TransmissionMedium, VesselType
from pydantic import BaseModel
import asyncio

router = APIRouter(tags=["sos"])

# Simple in-memory pubsub for websockets
active_connections: List[WebSocket] = []

async def broadcast_event(event_data: dict):
    for connection in active_connections.copy():
        try:
            await connection.send_json(event_data)
        except:
            active_connections.remove(connection)

class SOSTriggerPayload(BaseModel):
    vessel_id: uuid.UUID
    lat: float
    lon: float
    incident_type: IncidentType = IncidentType.SOS
    description: str = ""
    client_event_id: Optional[str] = None
    captured_at_device: Optional[datetime] = None
    transmission_medium: TransmissionMedium = TransmissionMedium.CELLULAR
    transmission_latency_ms: Optional[int] = None

def _is_terminal(state: str) -> bool:
    return state in [IncidentStatus.RESCUED, IncidentStatus.CANCELLED, IncidentStatus.RESOLVED]

def validate_transition(current_state: str, next_state: str):
    if _is_terminal(current_state):
        raise HTTPException(400, f"Cannot transition from terminal state {current_state}")
    
    # Allow logic mapping
    # ACTIVE -> CAPSIZED, SAR_ACTIVE, RESCUED, CANCELLED
    # CAPSIZED -> SAR_ACTIVE, RESCUED, CANCELLED
    # SAR_ACTIVE -> RESCUED, CANCELLED
    
    allowed = {
        IncidentStatus.ACTIVE: [IncidentStatus.CAPSIZED, IncidentStatus.SAR_ACTIVE, IncidentStatus.RESCUED, IncidentStatus.CANCELLED, IncidentStatus.RESOLVED],
        IncidentStatus.CAPSIZED: [IncidentStatus.SAR_ACTIVE, IncidentStatus.RESCUED, IncidentStatus.CANCELLED, IncidentStatus.RESOLVED],
        IncidentStatus.SAR_ACTIVE: [IncidentStatus.RESCUED, IncidentStatus.CANCELLED, IncidentStatus.RESOLVED],
        IncidentStatus.INVESTIGATING: [IncidentStatus.ACTIVE, IncidentStatus.CANCELLED]
    }
    
    if current_state in allowed and next_state not in allowed[current_state]:
        raise HTTPException(400, f"Invalid transition: {current_state} -> {next_state}")


@router.post("/api/v1/sos/trigger")
async def trigger_sos(payload: SOSTriggerPayload, db: AsyncSession = Depends(get_db)):
    if payload.client_event_id:
        existing = await db.execute(
            select(IncidentORM).where(
                IncidentORM.vessel_id == payload.vessel_id,
                IncidentORM.description.like(f"%{payload.client_event_id}%")
            )
        )
        existing_incident = existing.scalar_one_or_none()
        if existing_incident:
            return existing_incident
            
    incident_id = uuid.uuid4()
    
    lkp_t = payload.captured_at_device if payload.captured_at_device else datetime.utcnow()
    desc = payload.description
    if payload.client_event_id:
        desc = f"{desc} [client_event_id={payload.client_event_id}]"

    incident = IncidentORM(
        id=incident_id,
        vessel_id=payload.vessel_id,
        incident_type=payload.incident_type,
        status=IncidentStatus.ACTIVE,
        lkp_lat=payload.lat,
        lkp_lon=payload.lon,
        lkp_time=lkp_t,
        description=desc,
        transmission_medium=payload.transmission_medium,
        transmission_latency_ms=payload.transmission_latency_ms
    )
    db.add(incident)
    await db.commit()
    await db.refresh(incident)
    
    event = {
        "event": "SOS_TRIGGERED",
        "incident_id": str(incident_id),
        "vessel_id": str(payload.vessel_id),
        "lat": payload.lat,
        "lon": payload.lon,
        "timestamp": datetime.utcnow().isoformat(),
        "state": IncidentStatus.ACTIVE,
        "is_simulated": True,
        "transmission_medium": payload.transmission_medium,
        "transmission_latency_ms": payload.transmission_latency_ms
    }
    await broadcast_event(event)
    
    # Notify ORCA to begin SAR analysis async
    asyncio.create_task(run_sar_analysis(incident_id))
    
    return incident

@router.post("/api/v1/sos/{incident_id}/transition")
async def transition_incident(incident_id: uuid.UUID, next_state: IncidentStatus, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IncidentORM).where(IncidentORM.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(404, "Incident not found")
        
    validate_transition(incident.status, next_state)
    
    incident.status = next_state
    
    # If capsized, also update type to reflect it
    if next_state == IncidentStatus.CAPSIZED:
        incident.incident_type = IncidentType.CAPSIZE
        
    await db.commit()
    
    await broadcast_event({
        "event": f"STATE_TRANSITION_{next_state}",
        "incident_id": str(incident_id),
        "new_state": next_state,
        "timestamp": datetime.utcnow().isoformat(),
        "is_simulated": True
    })
    
    return {"status": "success", "new_state": next_state}

@router.post("/api/v1/sos/cancel")
async def cancel_sos(incident_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IncidentORM).where(IncidentORM.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(404)
        
    validate_transition(incident.status, IncidentStatus.CANCELLED)
    
    incident.status = IncidentStatus.CANCELLED
    await db.commit()
    
    await broadcast_event({
        "event": "SOS_CANCELLED",
        "incident_id": str(incident_id),
        "state": IncidentStatus.CANCELLED
    })
    return {"status": "cancelled"}

@router.post("/api/v1/sos/{incident_id}/rescue")
async def rescue_sos(incident_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IncidentORM).where(IncidentORM.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(404)
        
    validate_transition(incident.status, IncidentStatus.RESCUED)
    
    incident.status = IncidentStatus.RESCUED
    await db.commit()
    
    await broadcast_event({
        "event": "SOS_RESCUED",
        "incident_id": str(incident_id),
        "state": IncidentStatus.RESCUED
    })
    return {"status": "rescued"}

@router.post("/api/v1/sos/{incident_id}/acknowledge")
async def acknowledge_sos(incident_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IncidentORM).where(IncidentORM.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(404)
    # Status remains unchanged, but we broadcast the acknowledgement
    await broadcast_event({
        "event": "SOS_ACKNOWLEDGED",
        "incident_id": str(incident_id)
    })
    return {"status": "acknowledged"}

@router.get("/api/v1/sos/{incident_id}")
async def get_sos(incident_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IncidentORM).where(IncidentORM.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(404)
    return incident

@router.get("/api/v1/sos")
async def get_all_sos(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IncidentORM).order_by(IncidentORM.created_at.desc()))
    return result.scalars().all()

async def run_sar_analysis(incident_id: uuid.UUID):
    await broadcast_event({"event": "SAR_ANALYSIS_STARTED", "incident_id": str(incident_id)})
    
    from core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(IncidentORM).where(IncidentORM.id == incident_id))
        incident = result.scalar_one_or_none()
        if not incident:
            return
            
        try:
            from packages.orca_agents.models import SARPlanningContext
            from packages.orca_agents.orchestrator import SAROrchestrator
            
            ctx = SARPlanningContext(
                incident_id=str(incident_id),
                vessel_id=str(incident.vessel_id),
                lat=incident.lkp_lat,
                lon=incident.lkp_lon,
                timestamp=incident.lkp_time.isoformat(),
                emergency_type=incident.incident_type
            )
            
            sar_final_result = await SAROrchestrator.execute_sar_workflow(ctx)
            
            # Transition to SAR_ACTIVE automatically
            if not _is_terminal(incident.status) and incident.status != IncidentStatus.SAR_ACTIVE:
                incident.status = IncidentStatus.SAR_ACTIVE
            
            from core.db_models import ORCASessionORM, AgentTaskORM
            from models import SessionStatus, AgentTaskStatus
            
            session_id = uuid.uuid4()
            orca_session = ORCASessionORM(
                id=session_id,
                incident_id=incident_id,
                user_query="Automated SAR analysis via SOS trigger",
                status=SessionStatus.DONE,
                evidence=sar_final_result.evidence if hasattr(sar_final_result, "evidence") else []
            )
            db.add(orca_session)
            
            # Associate incident to session
            incident.orca_session_id = session_id
            
            for trace_idx, t in enumerate(sar_final_result.agent_trace):
                # We save each agent's execution step as a task
                task_status_str = str(t.get("status", "success")).upper()
                
                # Check valid AgentTaskStatus
                if task_status_str == "SUCCESS":
                    st = AgentTaskStatus.DONE
                else:
                    st = AgentTaskStatus.ERROR
                    
                task = AgentTaskORM(
                    session_id=session_id,
                    agent_name=t.get("agent", "Unknown"),
                    tool_name="execution",
                    status=st,
                    error_msg=str(t.get("errors")) if t.get("errors") else None,
                    output_payload={"summary": t.get("summary", "")},
                    started_at=datetime.utcnow(),
                    finished_at=datetime.utcnow()
                )
                db.add(task)

            predictions = sar_final_result.sar_predictions
            for p in predictions:
                d = DriftPredictionORM(
                    incident_id=incident_id,
                    session_id=session_id,
                    horizon_h=p["horizon_hours"],
                    predicted_lat=p["position"]["lat"],
                    predicted_lon=p["position"]["lon"],
                    algorithm="RK4-v1",
                    sim_label="SIMULATED"
                )
                db.add(d)
                
            await db.commit()
            
            await broadcast_event({
                "event": "DRIFT_UPDATED",
                "incident_id": str(incident_id),
                "predictions": predictions,
                "state": incident.status,
                "agent_trace": sar_final_result.agent_trace
            })
            
            await broadcast_event({
                "event": "MAYDAY_BROADCAST",
                "incident_id": str(incident_id),
                "message": sar_final_result.communications.get("message", "VESSEL IN DISTRESS"),
                "is_simulated": True
            })
        except BaseException as e:
            print("SAR error:", e)

# Authority Endpoints
@router.get("/api/v1/authority/incidents")
async def auth_get_incidents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IncidentORM))
    return result.scalars().all()

@router.get("/api/v1/authority/incidents/{incident_id}")
async def auth_get_incident(incident_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IncidentORM).where(IncidentORM.id == incident_id))
    return result.scalar_one_or_none()

@router.get("/api/v1/authority/incidents/{incident_id}/sar")
async def auth_get_incident_sar(incident_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DriftPredictionORM).where(DriftPredictionORM.incident_id == incident_id))
    preds = result.scalars().all()
    from packages.sar_physics.rk4 import generate_search_cone
    
    # Mangle to expected Phase 9 shape for search cone
    p_dicts = [{"horizon_hours": p.horizon_h, "position": {"lat": p.predicted_lat, "lon": p.predicted_lon}, "uncertainty_radius_nm": 5.0} for p in preds]
    cone = generate_search_cone(p_dicts)
    
    return {
        "incident_id": str(incident_id),
        "predictions": preds,
        "search_areas": cone,
        "is_simulated": True
    }

@router.websocket("/ws/authority")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

@router.post("/api/v1/demo/reset")
async def reset_demo(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import delete
    from core.db_models import VesselORM
    await db.execute(delete(DriftPredictionORM))
    await db.execute(delete(IncidentORM))
    
    # 3 deterministic demo incidents
    incidents = [
        IncidentORM(
            id=uuid.uuid4(),
            vessel_id=uuid.UUID("11111111-0000-0000-0000-000000000001"),
            incident_type=IncidentType.SOS,
            status=IncidentStatus.ACTIVE,
            lkp_lat=12.5,
            lkp_lon=80.8,
            lkp_time=datetime.utcnow(),
            description="[DEMO] Fishing Vessel Engine Failure: Fishing vessel reports engine failure and requests immediate assistance."
        ),
        IncidentORM(
            id=uuid.uuid4(),
            vessel_id=uuid.UUID("11111111-0000-0000-0000-000000000002"),
            incident_type=IncidentType.COMMS_LOSS,
            status=IncidentStatus.ACTIVE,
            lkp_lat=13.0,
            lkp_lon=81.2,
            lkp_time=datetime.utcnow(),
            description="[DEMO] Vessel Communication Lost: Fishing vessel stopped responding to scheduled communication checks. Last known position available."
        ),
        IncidentORM(
            id=uuid.uuid4(),
            vessel_id=uuid.UUID("11111111-0000-0000-0000-000000000003"),
            incident_type=IncidentType.SOS,  # Mapped to SOS since MEDICAL_EMERGENCY enum might not exist in db
            status=IncidentStatus.ACTIVE,
            lkp_lat=13.3,
            lkp_lon=80.6,
            lkp_time=datetime.utcnow(),
            description="[DEMO] Medical Emergency Onboard: Crew member reported a medical emergency and requested coastal authority assistance."
        )
    ]
    
    # Ensure vessels exist first or fallback
    vessels_to_ensure = [
        VesselORM(id=uuid.UUID("11111111-0000-0000-0000-000000000001"), mmsi="419000001", name="MFV Saraswati", vessel_type=VesselType.FISHING_ARTISANAL),
        VesselORM(id=uuid.UUID("11111111-0000-0000-0000-000000000002"), mmsi="419000002", name="MFV Lakshmi Devi", vessel_type=VesselType.FISHING_MECHANISED),
        VesselORM(id=uuid.UUID("11111111-0000-0000-0000-000000000003"), mmsi="419000003", name="MFV Durga Mata", vessel_type=VesselType.FISHING_ARTISANAL),
    ]
    for v in vessels_to_ensure:
        existing = await db.get(VesselORM, v.id)
        if not existing:
            db.add(v)
            
    await db.flush()
    
    for inc in incidents:
        db.add(inc)
            
    await db.commit()
    
    await broadcast_event({
        "event": "DEMO_RESET"
    })
    return {"status": "success", "message": "Demo data reset successfully"}
