"""
ORCA — SQLAlchemy Database Models (ORM)
=====================================================
These are the DB-side table definitions.
Pydantic models in packages/shared-types/models.py are the API schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from geoalchemy2 import Geometry
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

import sys
import os

# Allow importing from packages/shared-types
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "shared-types"))
from models import (
    AgentTaskStatus,
    IncidentStatus,
    IncidentType,
    MessageRole,
    SessionStatus,
    VesselType,
    ZoneType,
)


class Base(DeclarativeBase):
    pass


# ============================================================
# Vessel
# ============================================================


class VesselORM(Base):
    __tablename__ = "vessels"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    mmsi: Mapped[Optional[str]] = mapped_column(String(9), nullable=True, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    vessel_type: Mapped[str] = mapped_column(
        Enum(VesselType, name="vessel_type_enum"), default=VesselType.FISHING_ARTISANAL
    )
    transponder_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Current position (nullable — vessel may not have reported yet)
    lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    heading: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    speed_kts: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    incidents: Mapped[list["IncidentORM"]] = relationship("IncidentORM", back_populates="vessel")


# ============================================================
# Incident
# ============================================================


class IncidentORM(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    vessel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vessels.id"), nullable=False
    )
    incident_type: Mapped[str] = mapped_column(
        Enum(IncidentType, name="incident_type_enum"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum(IncidentStatus, name="incident_status_enum"), default=IncidentStatus.ACTIVE
    )
    lkp_lat: Mapped[float] = mapped_column(Float, nullable=False)
    lkp_lon: Mapped[float] = mapped_column(Float, nullable=False)
    lkp_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transmission_medium: Mapped[str] = mapped_column(String(50), default="CELLULAR")
    transmission_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    orca_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    vessel: Mapped["VesselORM"] = relationship("VesselORM", back_populates="incidents")
    drift_predictions: Mapped[list["DriftPredictionORM"]] = relationship(
        "DriftPredictionORM", back_populates="incident"
    )


# ============================================================
# ORCA Session
# ============================================================


class ORCASessionORM(Base):
    __tablename__ = "orca_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=True
    )
    user_query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    detected_language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    messages: Mapped[list[Any]] = mapped_column(JSON, default=list)
    plan: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    evidence: Mapped[list[Any]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(
        Enum(SessionStatus, name="session_status_enum"), default=SessionStatus.PLANNING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    agent_tasks: Mapped[list["AgentTaskORM"]] = relationship(
        "AgentTaskORM", back_populates="session"
    )


# ============================================================
# Agent Task
# ============================================================


class AgentTaskORM(Base):
    __tablename__ = "agent_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orca_sessions.id"), nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(AgentTaskStatus, name="agent_task_status_enum"),
        default=AgentTaskStatus.PENDING,
    )
    input_payload: Mapped[Any] = mapped_column(JSON, default=dict)
    output_payload: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_msg: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    session: Mapped["ORCASessionORM"] = relationship("ORCASessionORM", back_populates="agent_tasks")


# ============================================================
# Drift Prediction
# ============================================================


class DriftPredictionORM(Base):
    __tablename__ = "drift_predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False
    )
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    horizon_h: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_lat: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_lon: Mapped[float] = mapped_column(Float, nullable=False)
    drift_polygon: Mapped[Optional[Any]] = mapped_column(
        Geometry("POLYGON", srid=4326), nullable=True
    )
    force_breakdown: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    algorithm: Mapped[str] = mapped_column(String(50), default="RK4-v1")
    sim_label: Mapped[str] = mapped_column(
        String(200), default="SIMULATED — not real INCOIS/IMD data"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    incident: Mapped["IncidentORM"] = relationship(
        "IncidentORM", back_populates="drift_predictions"
    )


# ============================================================
# Weather Snapshot
# ============================================================


class WeatherSnapshotORM(Base):
    __tablename__ = "weather_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_label: Mapped[str] = mapped_column(String(100), nullable=False)
    fetch_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    radius_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wind_speed_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wind_dir_deg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wave_height_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sea_temp_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_speed_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_dir_deg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    raw_payload: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True)


# ============================================================
# Geofence Zone
# ============================================================


class GeofenceZoneORM(Base):
    __tablename__ = "geofence_zones"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    zone_type: Mapped[str] = mapped_column(
        Enum(ZoneType, name="zone_type_enum"), nullable=False
    )
    boundary: Mapped[Any] = mapped_column(
        Geometry("MULTIPOLYGON", srid=4326), nullable=False
    )
    alert_buffer_nm: Mapped[float] = mapped_column(Float, default=2.0)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    authority: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ============================================================
# H3 Cache Cell
# ============================================================


class H3CellORM(Base):
    __tablename__ = "h3_cells"

    h3_index: Mapped[str] = mapped_column(String(20), primary_key=True)
    resolution: Mapped[int] = mapped_column(Integer, nullable=False)
    forecast_payload: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    cached_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
