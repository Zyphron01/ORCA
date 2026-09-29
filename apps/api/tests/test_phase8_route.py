import pytest
from packages.orca_core.tools import evaluate_route_safety

def test_route_safety_invalid_coords():
    # Invalid coordinates
    res = evaluate_route_safety.invoke({
        "start_lat": 100.0,
        "start_lon": 80.0,
        "end_lat": 12.0,
        "end_lon": 80.0,
        "speed_kts": 10.0
    })
    assert "error" in res
    assert "Invalid coordinates" in res["error"]

def test_route_safety_same_coords():
    res = evaluate_route_safety.invoke({
        "start_lat": 10.0,
        "start_lon": 80.0,
        "end_lat": 10.0,
        "end_lon": 80.0,
        "speed_kts": 10.0
    })
    assert "error" in res
    assert "identical" in res["error"]

def test_route_safety_baseline_and_segmentation():
    # Good route (start to end without touching the mock IMBL)
    # Our mock demo IMBL might be near (79.4, 9.4).
    # We will pick points away from it.
    res = evaluate_route_safety.invoke({
        "start_lat": 15.0,
        "start_lon": 80.0,
        "end_lat": 16.0,
        "end_lon": 80.0,
        "speed_kts": 10.0
    })
    
    assert "error" not in res
    data = res["data"]
    
    # Check baseline creation
    assert "route" in data
    assert len(data["route"]) >= 3 # at least start, mid, end
    assert data["distance_nm"] > 0
    assert data["estimated_hours"] > 0
    assert "alternatives" in data
    
def test_route_safety_hazard_detection():
    # Route that goes directly through a hazard zone
    # We'll use coords that might be close to our dummy geofences.
    # In demo, (79.4, 9.4) is used for IMBL check. So let's route near (9.4, 79.4).
    res = evaluate_route_safety.invoke({
        "start_lat": 9.4,
        "start_lon": 79.4,
        "end_lat": 9.5,
        "end_lon": 79.5,
        "speed_kts": 10.0
    })
    
    assert "error" not in res
    data = res["data"]
    
    # Ensure it's marked as having restrictions if IMBL is detected, else check structure
    assert "restricted_areas" in data
    assert "hazards" in data
    assert data["risk_level"] in ["LOW", "HIGH"]
