import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from main import app
from core.database import get_db
from models import IncidentStatus, IncidentType

mock_session = AsyncMock()

def override_get_db():
    yield mock_session

client = TestClient(app)

@pytest.fixture(autouse=True)
def override_dependencies():
    app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def mock_incident():
    inc = MagicMock()
    inc.id = uuid.uuid4()
    inc.vessel_id = uuid.uuid4()
    inc.status = IncidentStatus.ACTIVE
    inc.incident_type = IncidentType.SOS
    inc.lkp_lat = 10.0
    inc.lkp_lon = 80.0
    return inc

def test_sos_activation():
    vessel_id = str(uuid.uuid4())
    mock_session.commit = AsyncMock()
    
    with patch("routers.sos.broadcast_event"):
        with patch("routers.sos.run_sar_analysis"):
            response = client.post("/api/v1/sos/trigger", json={
                "vessel_id": vessel_id,
                "lat": 12.0,
                "lon": 80.0,
                "description": "Engine failure"
            })
        
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == IncidentStatus.ACTIVE
    assert data["incident_type"] == IncidentType.SOS

def test_valid_capsize_transition(mock_incident):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_incident
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    
    with patch("routers.sos.broadcast_event"):
        response = client.post(f"/api/v1/sos/{mock_incident.id}/transition?next_state={IncidentStatus.CAPSIZED.value}")
        
    assert response.status_code == 200
    assert response.json()["new_state"] == IncidentStatus.CAPSIZED

def test_valid_cancel_transition(mock_incident):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_incident
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    
    with patch("routers.sos.broadcast_event"):
        response = client.post(f"/api/v1/sos/cancel?incident_id={mock_incident.id}")
        
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

def test_invalid_terminal_transition(mock_incident):
    mock_incident.status = IncidentStatus.RESCUED
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_incident
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    response = client.post(f"/api/v1/sos/{mock_incident.id}/transition?next_state={IncidentStatus.CAPSIZED.value}")
    
    assert response.status_code == 400
    assert "Cannot transition from terminal state" in response.json()["detail"]

def test_invalid_state_transition(mock_incident):
    mock_incident.status = IncidentStatus.ACTIVE
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_incident
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    response = client.post(f"/api/v1/sos/{mock_incident.id}/transition?next_state={IncidentStatus.INVESTIGATING.value}")
    
    assert response.status_code == 400
    assert "Invalid transition" in response.json()["detail"]

def test_rescue_completion(mock_incident):
    mock_incident.status = IncidentStatus.SAR_ACTIVE
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_incident
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    
    with patch("routers.sos.broadcast_event"):
        response = client.post(f"/api/v1/sos/{mock_incident.id}/rescue")
        
    assert response.status_code == 200
    assert response.json()["status"] == "rescued"

def test_orca_manage_emergency_tool():
    from packages.orca_core.tools import manage_emergency
    
    res = manage_emergency.invoke({
        "action": "TRIGGER",
        "vessel_id": str(uuid.uuid4()),
        "lat": 10.0,
        "lon": 80.0
    })
    
    assert res["is_simulated"] is True
    # If DB not present, it mocks, but here it might use the actual DB if import succeeds.
    # We just check the structure.
    assert "data" in res
    assert "incident_id" in res["data"] or "status" in res["data"]
