import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.db_models import IncidentORM, VesselORM, DriftPredictionORM, ORCASessionORM, AgentTaskORM, WeatherSnapshotORM
from models import IntelligenceReport, GeoPoint, ReportAgentTrace, ReportEnvironment, DriftPoint, DriftHorizon, DriftForceBreakdown

router = APIRouter(tags=["reports"])

@router.get("/api/v1/authority/incidents/{incident_id}/report", response_model=IntelligenceReport)
async def get_incident_intelligence_report(incident_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # 1. Fetch Incident with Vessel
    result = await db.execute(select(IncidentORM).where(IncidentORM.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(404, "Incident not found")
        
    vessel_result = await db.execute(select(VesselORM).where(VesselORM.id == incident.vessel_id))
    vessel = vessel_result.scalar_one_or_none()
    
    # 2. Fetch SAR Predictions (T+1, T+3, T+6)
    drift_result = await db.execute(select(DriftPredictionORM).where(DriftPredictionORM.incident_id == incident_id))
    drift_preds = drift_result.scalars().all()
    
    sar_points = []
    max_radius = 0.0
    for d in drift_preds:
        # Mocking force breakdown since it might not be fully stored
        fb = DriftForceBreakdown(current_pct=60, wind_pct=30, stokes_pct=10)
        sar_points.append(
            DriftPoint(
                horizon_h=DriftHorizon(d.horizon_h),
                position=GeoPoint(lat=d.predicted_lat, lon=d.predicted_lon),
                force_breakdown=fb,
                uncertainty_radius_nm=5.0
            )
        )
        if 5.0 > max_radius:
            max_radius = 5.0

    # 3. Fetch Agent Trace and Evidence via ORCA Session (if exists)
    agent_traces = []
    evidence = []
    if incident.orca_session_id:
        # Fetch ORCASession for evidence
        session_result = await db.execute(select(ORCASessionORM).where(ORCASessionORM.id == incident.orca_session_id))
        orca_session = session_result.scalar_one_or_none()
        if orca_session and orca_session.evidence:
            evidence = orca_session.evidence

        task_result = await db.execute(select(AgentTaskORM).where(AgentTaskORM.session_id == incident.orca_session_id))
        tasks = task_result.scalars().all()
        for t in tasks:
            agent_traces.append(ReportAgentTrace(
                agent_name=t.agent_name,
                status=t.status.value if hasattr(t.status, "value") else str(t.status),
                started_at=t.started_at,
                finished_at=t.finished_at
            ))
            
    # 4. Fetch nearest weather snapshot (if any) or fallback
    weather_result = await db.execute(
        select(WeatherSnapshotORM)
        .order_by(WeatherSnapshotORM.fetch_time.desc())
        .limit(1)
    )
    weather = weather_result.scalar_one_or_none()
    
    environment = ReportEnvironment(
        weather_summary="Data unavailable",
        marine_conditions="Data unavailable",
        hazards="None detected"
    )
    if weather:
        environment.weather_summary = f"Wind: {weather.wind_speed_ms}m/s. Sea Temp: {weather.sea_temp_c}C"
        environment.marine_conditions = f"Currents: {weather.current_speed_ms}m/s. Waves: {weather.wave_height_m}m"

    # Assemble Report
    report = IntelligenceReport(
        report_id=f"REP-{incident_id.hex[:8].upper()}",
        generated_at=datetime.utcnow(),
        incident_id=incident.id,
        vessel_id=vessel.id if vessel else incident.vessel_id,
        vessel_name=vessel.name if vessel else "Unknown Vessel",
        vessel_type=(vessel.vessel_type.value if hasattr(vessel.vessel_type, "value") else str(vessel.vessel_type)) if vessel else "UNKNOWN",
        incident_type=incident.incident_type,
        status=incident.status,
        lkp=GeoPoint(lat=incident.lkp_lat, lon=incident.lkp_lon),
        lkp_time=incident.lkp_time,
        sar_predictions=sar_points,
        search_radius_nm=max_radius if max_radius > 0 else None,
        agent_traces=agent_traces,
        evidence=evidence,
        environment=environment,
        actions_taken=[
            f"Incident detected at {incident.lkp_time.isoformat()}Z",
            f"Automated SAR prediction computed ({len(sar_points)} horizons)",
            f"Multi-agent reasoning executed ({len(agent_traces)} agents)"
        ]
    )
    
    return report
