"""
ORCA — Vessels Router
GET  /api/v1/vessels
GET  /api/v1/vessels/{vessel_id}
POST /api/v1/vessels
POST /api/v1/vessels/{vessel_id}/sos
"""

from __future__ import annotations

import uuid
import sys
import os
from datetime import datetime
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "shared-types"))

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Vessel, VesselCreate, VesselUpdate, GeoPoint, SOSTrigger, SOSAck
from core.database import get_db
from core.db_models import VesselORM, IncidentORM
from models import IncidentType, IncidentStatus

router = APIRouter(prefix="/api/v1/vessels", tags=["vessels"])


def _orm_to_vessel(v: VesselORM) -> Vessel:
    position = None
    if v.lat is not None and v.lon is not None:
        position = GeoPoint(lat=v.lat, lon=v.lon)
    return Vessel(
        id=v.id,
        mmsi=v.mmsi,
        name=v.name,
        owner_name=v.owner_name,
        vessel_type=v.vessel_type,
        transponder_id=v.transponder_id,
        position=position,
        heading=v.heading,
        speed_kts=v.speed_kts,
        last_seen_at=v.last_seen_at,
        is_active=v.is_active,
        created_at=v.created_at,
        updated_at=v.updated_at,
    )


@router.get("", response_model=List[Vessel], summary="List all vessels")
async def list_vessels(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
) -> List[Vessel]:
    stmt = select(VesselORM)
    if active_only:
        stmt = stmt.where(VesselORM.is_active == True)
    result = await db.execute(stmt)
    vessels = result.scalars().all()
    return [_orm_to_vessel(v) for v in vessels]


@router.get("/{vessel_id}", response_model=Vessel, summary="Get vessel by ID")
async def get_vessel(
    vessel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Vessel:
    result = await db.execute(select(VesselORM).where(VesselORM.id == vessel_id))
    vessel = result.scalar_one_or_none()
    if vessel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vessel not found")
    return _orm_to_vessel(vessel)


@router.post("", response_model=Vessel, status_code=status.HTTP_201_CREATED, summary="Register vessel")
async def create_vessel(
    data: VesselCreate,
    db: AsyncSession = Depends(get_db),
) -> Vessel:
    vessel = VesselORM(
        id=uuid.uuid4(),
        mmsi=data.mmsi,
        name=data.name,
        owner_name=data.owner_name,
        vessel_type=data.vessel_type,
        transponder_id=data.transponder_id,
    )
    db.add(vessel)
    await db.flush()
    await db.refresh(vessel)
    return _orm_to_vessel(vessel)


@router.post("/{vessel_id}/sos", response_model=SOSAck, summary="Trigger SOS from vessel")
async def trigger_sos(
    vessel_id: uuid.UUID,
    trigger: SOSTrigger,
    db: AsyncSession = Depends(get_db),
) -> SOSAck:
    # Verify vessel exists
    result = await db.execute(select(VesselORM).where(VesselORM.id == vessel_id))
    vessel = result.scalar_one_or_none()
    if vessel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vessel not found")

    # Create incident
    incident_id = uuid.uuid4()
    session_id = uuid.uuid4()
    incident = IncidentORM(
        id=incident_id,
        vessel_id=vessel_id,
        incident_type=IncidentType.SOS,
        status=IncidentStatus.ACTIVE,
        lkp_lat=trigger.position.lat,
        lkp_lon=trigger.position.lon,
        lkp_time=datetime.utcnow(),
        description=trigger.description or f"SOS triggered: {trigger.trigger_type}",
        orca_session_id=session_id,
    )
    db.add(incident)
    await db.flush()

    return SOSAck(
        incident_id=incident_id,
        session_id=session_id,
        message=(
            f"SOS received from vessel '{vessel.name}'. "
            f"Last Known Position locked at {trigger.position.lat:.4f}°N, {trigger.position.lon:.4f}°E. "
            f"ORCA is initializing rescue workflow. [DEMO MODE]"
        ),
        estimated_response_min=15,
    )
