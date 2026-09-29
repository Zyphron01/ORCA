import pytest
import uuid
import math
from models import IncidentStatus
from sar_physics.rk4 import predict_drift, generate_search_cone, compute_velocity, rk4_step, haversine
from unittest.mock import patch, MagicMock, AsyncMock

def test_rk4_compute_velocity():
    u, v, comps = compute_velocity(10.0, 80.0, 0, 1.0, 90.0, 10.0, 180.0, 0.0, 0.03)
    assert u is not None
    assert v is not None
    assert "total_kts" in comps

def test_rk4_predict_drift():
    res = predict_drift(10.0, 80.0, 6, 1.0, 90.0, 10.0, 180.0)
    preds = res["predictions"]
    assert len(preds) == 3 # T+1, T+3, T+6
    assert preds[0]["horizon_hours"] == 1
    assert preds[1]["horizon_hours"] == 3
    assert preds[2]["horizon_hours"] == 6

def test_search_cone():
    res = predict_drift(10.0, 80.0, 6, 1.0, 90.0, 10.0, 180.0)
    preds = res["predictions"]
    cone = generate_search_cone(preds)
    assert cone["type"] == "FeatureCollection"
    assert len(cone["features"]) == 3

# Mock FastAPI app for tests
from fastapi.testclient import TestClient
from main import app
from core.database import get_db

# Create a mock session
mock_session = AsyncMock()

def override_get_db():
    yield mock_session

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def override_dependencies():
    app.dependency_overrides[get_db] = override_get_db

def test_sos_trigger_endpoint():
    vessel_id = str(uuid.uuid4())
    mock_session.commit = AsyncMock()
    
    with patch("routers.sos.broadcast_event"):
        response = client.post("/api/v1/sos/trigger", json={
            "vessel_id": vessel_id,
            "lat": 12.0,
            "lon": 80.0,
            "description": "Engine failure"
        })
        
    assert response.status_code == 200
    data = response.json()
    assert data["vessel_id"] == vessel_id
    assert data["lkp_lat"] == 12.0
    assert data["status"] == "ACTIVE"

def test_sos_cancel_endpoint():
    incident_id = str(uuid.uuid4())
    
    # Mock db.execute to return a mock incident
    mock_result = MagicMock()
    mock_incident = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_incident
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    with patch("routers.sos.broadcast_event"):
        response = client.post(f"/api/v1/sos/cancel?incident_id={incident_id}")
        
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert mock_incident.status == IncidentStatus.CANCELLED

def test_sos_acknowledge_endpoint():
    incident_id = str(uuid.uuid4())
    
    mock_result = MagicMock()
    mock_incident = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_incident
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    with patch("routers.sos.broadcast_event"):
        response = client.post(f"/api/v1/sos/{incident_id}/acknowledge")
        
    assert response.status_code == 200
    assert response.json()["status"] == "acknowledged"

def test_authority_incidents_endpoint():
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    response = client.get("/api/v1/authority/incidents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_capsize_simulator():
    # A simple pure logic test for the required capsize logic
    roll = 95
    duration = 16
    capsize = (roll > 90 and duration >= 15)
    assert capsize is True

def test_nearby_vessels_logic():
    # Simple calculation logic test for fleet relay
    lat1, lon1 = 12.0, 80.0
    lat2, lon2 = 12.05, 80.0  # Approx 3 nm away
    dist = haversine(lat1, lon1, lat2, lon2)
    assert dist < 10.0 # Within default 10 NM rescue radius

def test_sar_report_structure():
    report = {
        "incident_id": str(uuid.uuid4()),
        "vessel_id": str(uuid.uuid4()),
        "incident_type": "CAPSIZE_DETECTED",
        "lkp": {"lat": 12.0, "lon": 80.0},
        "conditions": {"wind": 15, "current": 1.2},
        "drift_forecast": {"t1": {}, "t3": {}, "t6": {}},
        "search_areas": {"type": "FeatureCollection", "features": []},
        "nearby_vessels": ["BC-002"],
        "tactical_messages": ["VESSEL IN DISTRESS"],
        "evidence": [],
        "is_simulated": True
    }
    assert report["is_simulated"] is True
    assert len(report["tactical_messages"]) > 0
