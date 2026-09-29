from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class SARPlanningContext(BaseModel):
    incident_id: str
    vessel_id: Optional[str]
    lat: float
    lon: float
    timestamp: str
    emergency_type: str = "SOS"

class SARAgentResult(BaseModel):
    agent: str
    status: str = "success"
    data: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    
class SARFinalResult(BaseModel):
    incident_id: str
    sar_predictions: List[Dict[str, Any]] = Field(default_factory=list)
    search_areas: Dict[str, Any] = Field(default_factory=dict)
    environment: Dict[str, Any] = Field(default_factory=dict)
    geospatial: Dict[str, Any] = Field(default_factory=dict)
    risks: List[str] = Field(default_factory=list)
    communications: Dict[str, Any] = Field(default_factory=dict)
    agent_trace: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    is_simulated: bool = True
