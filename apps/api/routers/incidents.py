"""
SAMUDRA-AI / ORCA — Incidents Router
POST  /api/v1/incidents
GET   /api/v1/incidents
GET   /api/v1/incidents/{id}
PATCH /api/v1/incidents/{id}
"""

from __future__ import annotations

import uuid
import sys
import os
from datetime import datetime
from typing import List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "shared-types"))

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Incident, IncidentCreate, GeoPoint, IncidentStatus
from core.database import get_db
from core.db_models import IncidentORM

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


def _orm_to_incident(inc: IncidentORM) -> Incident:
    return Incident(
        id=inc.id,
        vessel_id=inc.vessel_id,
        incident_type=inc.incident_type,
        status=inc.status,
        lkp=GeoPoint(lat=inc.lkp_lat, lon=inc.lkp_lon),
        lkp_time=inc.lkp_time,
        description=inc.description,
        orca_session_id=inc.orca_session_id,
        created_at=inc.created_at,
        updated_at=inc.updated_at,
    )


class IncidentStatusUpdate(BaseModel):
    status: IncidentStatus


@router.get("", response_model=List[Incident], summary="List incidents")
async def list_incidents(
    status_filter: Optional[IncidentStatus] = None,
    db: AsyncSession = Depends(get_db),
) -> List[Incident]:
    stmt = select(IncidentORM).order_by(IncidentORM.created_at.desc())
    if status_filter:
        stmt = stmt.where(IncidentORM.status == status_filter)
    result = await db.execute(stmt)
    incidents = result.scalars().all()
    return [_orm_to_incident(inc) for inc in incidents]


@router.post("", response_model=Incident, status_code=status.HTTP_201_CREATED, summary="Create incident")
async def create_incident(
    data: IncidentCreate,
    db: AsyncSession = Depends(get_db),
) -> Incident:
    incident = IncidentORM(
        id=uuid.uuid4(),
        vessel_id=data.vessel_id,
        incident_type=data.incident_type,
        status=IncidentStatus.ACTIVE,
        lkp_lat=data.lkp.lat,
        lkp_lon=data.lkp.lon,
        lkp_time=datetime.utcnow(),
        description=data.description,
    )
    db.add(incident)
    await db.flush()
    await db.refresh(incident)
    return _orm_to_incident(incident)


@router.get("/{incident_id}", response_model=Incident, summary="Get incident by ID")
async def get_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Incident:
    result = await db.execute(select(IncidentORM).where(IncidentORM.id == incident_id))
    incident = result.scalar_one_or_none()
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return _orm_to_incident(incident)


@router.patch("/{incident_id}", response_model=Incident, summary="Update incident status")
async def update_incident(
    incident_id: uuid.UUID,
    update: IncidentStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> Incident:
    result = await db.execute(select(IncidentORM).where(IncidentORM.id == incident_id))
    incident = result.scalar_one_or_none()
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    incident.status = update.status
    incident.updated_at = datetime.utcnow()
    await db.flush()
    return _orm_to_incident(incident)
