"""
ORCA — Shared Pydantic Type Definitions
=====================================================
All core data models used across the platform.
These models are the single source of truth for API contracts.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================
# Enumerations
# ============================================================


class IncidentType(str, enum.Enum):
    SOS = "SOS"
    CAPSIZE = "CAPSIZE"
    COMMS_LOSS = "COMMS_LOSS"
    GEOFENCE = "GEOFENCE"
    MAN_OVERBOARD = "MAN_OVERBOARD"


class IncidentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    FALSE_ALARM = "FALSE_ALARM"
    INVESTIGATING = "INVESTIGATING"
    
    # Phase 10 Emergency States
    CAPSIZED = "CAPSIZED"
    SAR_ACTIVE = "SAR_ACTIVE"
    RESCUED = "RESCUED"
    CANCELLED = "CANCELLED"


class VesselType(str, enum.Enum):
    FISHING_ARTISANAL = "FISHING_ARTISANAL"
    FISHING_MECHANISED = "FISHING_MECHANISED"
    COAST_GUARD = "COAST_GUARD"
    CARGO = "CARGO"
    PASSENGER = "PASSENGER"
    UNKNOWN = "UNKNOWN"


class AgentTaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    ERROR = "ERROR"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class SessionStatus(str, enum.Enum):
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    DONE = "DONE"
    ERROR = "ERROR"


class ZoneType(str, enum.Enum):
    IMBL = "IMBL"           # International Maritime Boundary Line
    MPA = "MPA"             # Marine Protected Area
    SHIPPING_LANE = "SHIPPING_LANE"
    RESTRICTED = "RESTRICTED"
    PFZ = "PFZ"             # Potential Fishing Zone


class DriftHorizon(int, enum.Enum):
    T1 = 1
    T3 = 3
    T6 = 6


# ============================================================
# Coordinate / Position
# ============================================================


class GeoPoint(BaseModel):
    """A WGS84 geographic coordinate."""

    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")

    @field_validator("lat")
    @classmethod
    def validate_lat(cls, v: float) -> float:
        if not (-90.0 <= v <= 90.0):
            raise ValueError(f"Latitude {v} out of range [-90, 90]")
        return round(v, 6)

    @field_validator("lon")
    @classmethod
    def validate_lon(cls, v: float) -> float:
        if not (-180.0 <= v <= 180.0):
            raise ValueError(f"Longitude {v} out of range [-180, 180]")
        return round(v, 6)


# ============================================================
# Vessel
# ============================================================


class VesselBase(BaseModel):
    mmsi: Optional[str] = Field(None, description="Maritime Mobile Service Identity (9 digits)")
    name: str = Field(..., min_length=1, max_length=100)
    owner_name: Optional[str] = None
    vessel_type: VesselType = VesselType.FISHING_ARTISANAL
    transponder_id: Optional[str] = None


class VesselCreate(VesselBase):
    pass


class VesselUpdate(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None
    heading: Optional[float] = None
    speed_kts: Optional[float] = None


class VesselPosition(BaseModel):
    vessel_id: uuid.UUID
    position: GeoPoint
    heading: Optional[float] = Field(None, ge=0, le=360)
    speed_kts: Optional[float] = Field(None, ge=0)
    timestamp: datetime


class Vessel(VesselBase):
    id: uuid.UUID
    position: Optional[GeoPoint] = None
    heading: Optional[float] = None
    speed_kts: Optional[float] = None
    last_seen_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# Incident
# ============================================================


class TransmissionMedium(str, enum.Enum):
    CELLULAR = "CELLULAR"
    SATELLITE_SIMULATION = "SATELLITE_SIMULATION"

class IncidentCreate(BaseModel):
    vessel_id: uuid.UUID
    incident_type: IncidentType
    lkp: GeoPoint
    description: Optional[str] = None
    transmission_medium: TransmissionMedium = TransmissionMedium.CELLULAR
    transmission_latency_ms: Optional[int] = None


class Incident(BaseModel):
    id: uuid.UUID
    vessel_id: uuid.UUID
    incident_type: IncidentType
    status: IncidentStatus = IncidentStatus.ACTIVE
    lkp: GeoPoint
    lkp_time: datetime
    description: Optional[str] = None
    transmission_medium: TransmissionMedium = TransmissionMedium.CELLULAR
    transmission_latency_ms: Optional[int] = None
    orca_session_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# ORCA Session / Chat
# ============================================================


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    language: Optional[str] = None           # ISO 639-1 code
    detected_language: Optional[str] = None
    tool_calls: Optional[list[dict[str, Any]]] = None
    created_at: Optional[datetime] = None


class ORCAQueryRequest(BaseModel):
    """Request to ORCA chat endpoint."""

    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[uuid.UUID] = Field(
        None, description="Pass existing session_id for multi-turn conversation"
    )
    language_hint: Optional[str] = Field(
        None, description="ISO 639-1 language hint (e.g. 'hi', 'ta', 'ml')"
    )
    incident_id: Optional[uuid.UUID] = Field(
        None, description="Attach this query to an active incident"
    )


class EvidenceItem(BaseModel):
    """Single piece of evidence in ORCA's reasoning chain."""

    type: Optional[str] = Field("generic", description="Type of evidence: sst, chlorophyll, pfz, weather, route, sar, etc.")
    asset_id: Optional[str] = Field(None, description="ID of the visual asset")
    value: Optional[float] = None
    unit: Optional[str] = None
    source: str  # e.g. "MOCK-INCOIS", "GEMINI-REAL"
    agent: str
    tool: str
    summary: str
    data: Optional[dict[str, Any]] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_simulated: bool = False
    evidence_context: Optional[dict[str, Any]] = None


class ORCAResponse(BaseModel):
    """Response from ORCA."""

    session_id: uuid.UUID
    message: str
    detected_language: Optional[str] = None
    evidence: list[EvidenceItem] = []
    plan: Optional[list[dict[str, Any]]] = None
    suggestions: Optional[list[str]] = None
    incident_id: Optional[uuid.UUID] = None
    visualization: Optional[dict[str, Any]] = None
    report: Optional[dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ORCASession(BaseModel):
    id: uuid.UUID
    incident_id: Optional[uuid.UUID] = None
    messages: list[ChatMessage] = []
    plan: Optional[list[dict[str, Any]]] = None
    evidence: list[EvidenceItem] = []
    status: SessionStatus = SessionStatus.PLANNING
    user_query: Optional[str] = None
    detected_language: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# Agent Task
# ============================================================


class AgentTask(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    agent_name: str
    tool_name: str
    status: AgentTaskStatus = AgentTaskStatus.PENDING
    input_payload: dict[str, Any] = {}
    output_payload: Optional[dict[str, Any]] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_msg: Optional[str] = None

    model_config = {"from_attributes": True}


# ============================================================
# Weather / Ocean Data
# ============================================================


class WindData(BaseModel):
    speed_ms: float = Field(..., description="Wind speed in m/s")
    direction_deg: float = Field(..., ge=0, le=360)
    gust_ms: Optional[float] = None
    source: str = "MOCK-IMD"
    is_simulated: bool = True
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class CurrentData(BaseModel):
    speed_ms: float = Field(..., description="Current speed in m/s")
    direction_deg: float = Field(..., ge=0, le=360)
    depth_m: float = Field(0.0, description="Surface = 0")
    source: str = "MOCK-INCOIS"
    is_simulated: bool = True
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class WaveData(BaseModel):
    significant_height_m: float = Field(..., description="Hs in metres")
    period_s: Optional[float] = None
    direction_deg: Optional[float] = None
    source: str = "MOCK-INCOIS"
    is_simulated: bool = True
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class WeatherSnapshot(BaseModel):
    """Consolidated weather/ocean state at a point."""

    position: GeoPoint
    wind: WindData
    current: CurrentData
    wave: WaveData
    sea_temp_c: Optional[float] = None
    chlorophyll_mgl: Optional[float] = None
    visibility_km: Optional[float] = None
    is_simulated: bool = True
    snapshot_time: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# Drift Prediction (RK4)
# ============================================================


class DriftForceBreakdown(BaseModel):
    current_pct: float = Field(..., ge=0, le=100)
    wind_pct: float = Field(..., ge=0, le=100)
    stokes_pct: float = Field(..., ge=0, le=100)

    @field_validator("stokes_pct")
    @classmethod
    def check_sum(cls, v: float, info: Any) -> float:
        data = info.data if hasattr(info, "data") else {}
        total = data.get("current_pct", 0) + data.get("wind_pct", 0) + v
        if abs(total - 100.0) > 1.0:
            raise ValueError(f"Force percentages must sum to 100, got {total}")
        return v


class DriftPoint(BaseModel):
    horizon_h: DriftHorizon
    position: GeoPoint
    force_breakdown: DriftForceBreakdown
    uncertainty_radius_nm: float = Field(..., description="1-sigma search radius in nautical miles")


class DriftPrediction(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    lkp: GeoPoint
    lkp_time: datetime
    predictions: list[DriftPoint]
    algorithm: str = "RK4-v1"
    sim_label: str = "SIMULATED — not real INCOIS/IMD data"
    computed_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


# ============================================================
# Geofence / Safety Zones
# ============================================================


class GeofenceZone(BaseModel):
    id: uuid.UUID
    name: str
    zone_type: ZoneType
    description: Optional[str] = None
    authority: Optional[str] = None
    alert_buffer_nm: float = Field(2.0, description="Alert distance in nautical miles")


class GeofenceCheckRequest(BaseModel):
    position: GeoPoint
    vessel_id: Optional[uuid.UUID] = None


class GeofenceCheckResult(BaseModel):
    position: GeoPoint
    in_zone: bool
    approaching_zone: bool
    nearest_zone: Optional[GeofenceZone] = None
    distance_nm: Optional[float] = None
    alert_message: Optional[str] = None


# ============================================================
# SOS Workflow
# ============================================================


class SOSTrigger(BaseModel):
    vessel_id: uuid.UUID
    position: GeoPoint
    trigger_type: str = Field(..., description="MANUAL, CAPSIZE, COMMS_LOSS")
    crew_count: Optional[int] = None
    description: Optional[str] = None


class SOSAck(BaseModel):
    incident_id: uuid.UUID
    session_id: uuid.UUID
    message: str
    estimated_response_min: Optional[int] = None


# ============================================================
# Health Check
# ============================================================


class HealthStatus(BaseModel):
    status: str = "ok"
    db: str = "ok"
    redis: str = "ok"
    version: str = "0.1.0"
    phase: str = "Phase 0 — Repository Scaffold"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# Intelligence Report (Phase 14)
# ============================================================


class ReportAgentTrace(BaseModel):
    agent_name: str
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class ReportEnvironment(BaseModel):
    weather_summary: Optional[str] = None
    marine_conditions: Optional[str] = None
    hazards: Optional[str] = None


class IntelligenceReport(BaseModel):
    report_id: str
    generated_at: datetime
    
    # Incident Context
    incident_id: uuid.UUID
    vessel_id: uuid.UUID
    vessel_name: str
    vessel_type: str
    incident_type: IncidentType
    status: IncidentStatus
    lkp: GeoPoint
    lkp_time: datetime
    
    # SAR Physics
    sar_predictions: list[DriftPoint] = []
    search_radius_nm: Optional[float] = None
    
    # Multi-Agent Analysis
    agent_traces: list[ReportAgentTrace] = []
    
    # Tactical
    environment: ReportEnvironment
    actions_taken: list[str] = []
    
    # Explainability
    evidence: list[EvidenceItem] = []
    
    model_config = {"from_attributes": True}
