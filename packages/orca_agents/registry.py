"""
ORCA — Agent Registry
"""
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AgentType(str, Enum):
    HYDRO_METEO = "HydroMeteo"
    MARINE_EO = "MarineEO"
    HAZARD_SENTRY = "HazardSentry"
    SAR_PHYSICS = "SARPhysics"
    TACTICAL_COMMS = "TacticalComms"
    SAR_PLANNER = "SARPlanner"
    RISK_SYNTHESIS = "RiskSynthesis"
    GEOSPATIAL = "Geospatial"

class AgentSpec(BaseModel):
    agent_id: str
    name: str
    description: str
    capabilities: List[str]
    tools: List[str]
    status: str
    input_requirements: Dict[str, str]
    output_type: str

AGENT_REGISTRY: Dict[AgentType, AgentSpec] = {
    AgentType.HYDRO_METEO: AgentSpec(
        agent_id="hydro_meteo",
        name="Hydro Meteo Agent",
        description="Agent for fetching and analyzing weather, wave, and ocean current data.",
        capabilities=["weather", "ocean_currents", "waves", "wind"],
        tools=["fetch_weather_forecast"],
        status="operational",
        input_requirements={"lat": "float", "lon": "float"},
        output_type="WeatherForecastData"
    ),
    AgentType.MARINE_EO: AgentSpec(
        agent_id="marine_eo",
        name="Marine Earth Observation Agent",
        description="Agent for Earth Observation data including PFZ, Chlorophyll, and SST.",
        capabilities=["pfz", "chlorophyll", "sst"],
        tools=["check_pfz_advisory"],
        status="operational",
        input_requirements={"lat": "float", "lon": "float"},
        output_type="PFZAdvisoryData"
    ),
    AgentType.HAZARD_SENTRY: AgentSpec(
        agent_id="hazard_sentry",
        name="Hazard Sentry Agent",
        description="Agent for monitoring geofences, IMBL boundaries, and restricted zones.",
        capabilities=["geofence", "imbl", "restricted_zones"],
        tools=["check_geofence_violations"],
        status="operational",
        input_requirements={"vessel_id": "str"},
        output_type="GeofenceViolationData"
    ),
    AgentType.SAR_PHYSICS: AgentSpec(
        agent_id="sar_physics",
        name="Search and Rescue Physics Agent",
        description="Agent for Search and Rescue physics and drift prediction models (RK4).",
        capabilities=["drift_prediction", "sar_routing"],
        tools=["calculate_drift_prediction"],
        status="operational",
        input_requirements={"incident_id": "str", "lkp_lat": "float", "lkp_lon": "float", "hours": "int"},
        output_type="DriftPredictionData"
    ),
    AgentType.TACTICAL_COMMS: AgentSpec(
        agent_id="tactical_comms",
        name="Tactical Communications Agent",
        description="Agent for managing communication channels (DAT-SG, NavIC, BLE).",
        capabilities=["dat_sg", "navic", "ble", "p2p_mesh", "message_formulation"],
        tools=[],
        status="operational",
        input_requirements={"risk_data": "dict", "sar_data": "dict"},
        output_type="CommsStatusData"
    ),
    AgentType.SAR_PLANNER: AgentSpec(
        agent_id="sar_planner",
        name="SAR Planning Agent",
        description="Agent for planning SAR tasks.",
        capabilities=["planning"],
        tools=[],
        status="operational",
        input_requirements={"incident_id": "str"},
        output_type="PlanData"
    ),
    AgentType.RISK_SYNTHESIS: AgentSpec(
        agent_id="risk_synthesis",
        name="Risk Agent",
        description="Agent for synthesizing risks.",
        capabilities=["risk_assessment"],
        tools=[],
        status="operational",
        input_requirements={},
        output_type="RiskData"
    ),
    AgentType.GEOSPATIAL: AgentSpec(
        agent_id="geospatial",
        name="Geospatial Agent",
        description="Agent for evaluating zones.",
        capabilities=["zoning", "context"],
        tools=[],
        status="operational",
        input_requirements={"lat": "float", "lon": "float"},
        output_type="GeospatialData"
    )
}

def get_agent_info(agent_type: AgentType) -> dict:
    """Retrieve metadata about a specialized agent."""
    agent = AGENT_REGISTRY.get(agent_type)
    return agent.model_dump() if agent else {}
