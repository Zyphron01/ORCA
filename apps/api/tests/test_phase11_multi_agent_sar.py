import pytest
import uuid
import asyncio
from unittest.mock import patch, MagicMock

from packages.orca_agents.registry import get_agent_info, AgentType
from packages.orca_agents.models import SARPlanningContext, SARAgentResult, SARFinalResult
from packages.orca_agents.orchestrator import SAROrchestrator
from packages.orca_agents.sar_agents import (
    SARPlanningAgent,
    SARPhysicsAgent,
    GeospatialAgent,
    EnvironmentAgent,
    RiskAgent,
    TacticalCommsAgent
)

@pytest.fixture
def mock_context():
    return SARPlanningContext(
        incident_id=str(uuid.uuid4()),
        vessel_id=str(uuid.uuid4()),
        lat=15.0,
        lon=73.0,
        timestamp="2026-09-26T12:00:00Z"
    )

def test_registry_discovery():
    agent_info = get_agent_info(AgentType.SAR_PLANNER)
    assert agent_info["agent_id"] == "sar_planner"
    assert "planning" in agent_info["capabilities"]
    
    agent_info = get_agent_info(AgentType.RISK_SYNTHESIS)
    assert agent_info["agent_id"] == "risk_synthesis"

@pytest.mark.asyncio
async def test_planning_agent(mock_context):
    result = await SARPlanningAgent.execute(mock_context)
    assert result.status == "success"
    assert result.agent == "SARPlanningAgent"
    assert "plan" in result.data

@pytest.mark.asyncio
@patch("packages.marine_data.get_providers")
async def test_environment_agent(mock_get_providers, mock_context):
    from unittest.mock import AsyncMock
    mock_weather = MagicMock()
    mock_weather.get_weather_forecast = AsyncMock(return_value=MagicMock(wind=MagicMock(speed_ms=10.0, direction_deg=180.0), current=MagicMock(speed_ms=0.5, direction_deg=90.0), wave=MagicMock(significant_height_m=1.5)))
    mock_ocean = MagicMock()
    mock_ocean.get_sea_state = AsyncMock(return_value={"sea_temp_c": 28.5})
    
    # Return mock providers
    mock_get_providers.return_value = (None, mock_weather, mock_ocean, None, None)
    
    result = await EnvironmentAgent.execute(mock_context)
    assert result.status == "success"
    assert result.agent == "EnvironmentAgent"
    assert result.data["wind_speed_ms"] == 10.0

@pytest.mark.asyncio
@patch("packages.marine_data.get_providers")
async def test_geospatial_agent(mock_get_providers, mock_context):
    from unittest.mock import AsyncMock
    mock_geo = MagicMock()
    mock_geo.get_spatial_context = AsyncMock(return_value={"h3_cell": "8960144b2c3ffff", "in_zones": []})
    mock_get_providers.return_value = (None, None, None, None, mock_geo)
    
    result = await GeospatialAgent.execute(mock_context)
    assert result.status == "success"
    assert result.data["h3_cell"] == "8960144b2c3ffff"

@pytest.mark.asyncio
async def test_sar_physics_agent(mock_context):
    env_data = {"current_speed_ms": 1.0, "current_dir_deg": 90.0, "wind_speed_ms": 5.0, "wind_dir_deg": 180.0, "wave_height_m": 1.0}
    result = await SARPhysicsAgent.execute(mock_context, env_data)
    assert result.status == "success"
    assert "predictions" in result.data
    assert "search_areas" in result.data
    assert len(result.data["predictions"]) > 0

@pytest.mark.asyncio
async def test_risk_agent(mock_context):
    env_data = {"wave_height_m": 3.0, "wind_speed_ms": 20.0}
    geo_data = {"in_zones": [{"name": "Hazard Zone A", "zone_type": "HAZARD"}]}
    sar_data = {}
    
    result = await RiskAgent.execute(mock_context, env_data, geo_data, sar_data)
    assert result.status == "success"
    assert len(result.data["risks"]) == 3
    assert any("High wave heights" in r for r in result.data["risks"])
    assert any("Strong winds" in r for r in result.data["risks"])
    assert any("Hazard Zone A" in r for r in result.data["risks"])

@pytest.mark.asyncio
async def test_tactical_comms_agent(mock_context):
    risk_data = {"risks": ["High waves"]}
    sar_data = {"predictions": [{"horizon_hours": 6, "position": {"lat": 15.1, "lon": 73.1}}]}
    result = await TacticalCommsAgent.execute(mock_context, risk_data, sar_data)
    assert result.status == "success"
    assert "MAYDAY RELAY" in result.data["message"]
    assert "15.1000, 73.1000" in result.data["message"]

@pytest.mark.asyncio
@patch("packages.marine_data.get_providers")
async def test_orchestrator_execution(mock_get_providers, mock_context):
    from unittest.mock import AsyncMock
    # Mocking for environment and geospatial
    mock_weather = MagicMock()
    mock_weather.get_weather_forecast = AsyncMock(return_value=MagicMock(wind=MagicMock(speed_ms=10.0, direction_deg=180.0), current=MagicMock(speed_ms=0.5, direction_deg=90.0), wave=MagicMock(significant_height_m=1.5)))
    mock_ocean = MagicMock()
    mock_ocean.get_sea_state = AsyncMock(return_value={"sea_temp_c": 28.5})
    mock_geo = MagicMock()
    mock_geo.get_spatial_context = AsyncMock(return_value={"h3_cell": "abc", "in_zones": []})
    
    mock_get_providers.return_value = (None, mock_weather, mock_ocean, None, mock_geo)
    
    result = await SAROrchestrator.execute_sar_workflow(mock_context)
    assert isinstance(result, SARFinalResult)
    assert result.incident_id == mock_context.incident_id
    assert len(result.agent_trace) == 6
    agent_names = [t["agent"] for t in result.agent_trace]
    assert "SARPlanningAgent" in agent_names
    assert "EnvironmentAgent" in agent_names
    assert "GeospatialAgent" in agent_names
    assert "SARPhysicsAgent" in agent_names
    assert "RiskAgent" in agent_names
    assert "TacticalCommsAgent" in agent_names
    
    assert len(result.sar_predictions) > 0
    assert result.environment["wind_speed_ms"] == 10.0
    assert "message" in result.communications

def test_orca_supervisor_tool(mock_context):
    from packages.orca_core.tools import run_sar_orchestration
    with patch("packages.orca_agents.orchestrator.SAROrchestrator.execute_sar_workflow") as mock_exec:
        mock_exec.return_value = SARFinalResult(
            incident_id=mock_context.incident_id,
            sar_predictions=[],
            search_areas={},
            environment={},
            geospatial={},
            risks=[],
            communications={},
            agent_trace=[]
        )
        
        # Test tool invocation
        res = run_sar_orchestration.invoke({
            "incident_id": mock_context.incident_id,
            "vessel_id": mock_context.vessel_id,
            "lat": mock_context.lat,
            "lon": mock_context.lon,
            "timestamp": mock_context.timestamp
        })
        
        assert res.get("status") == "success" or res.get("tool") == "run_sar_orchestration"
        assert res["is_simulated"] == True
