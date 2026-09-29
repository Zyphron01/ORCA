import pytest
from packages.sar_physics.rk4 import compute_velocity, rk4_step, predict_drift, generate_search_cone
from packages.orca_core.tools import calculate_drift_prediction

def test_compute_velocity_zero():
    u, v, comps = compute_velocity(10.0, 80.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    assert u == 0.0
    assert v == 0.0
    assert comps["total_kts"] == 0.0

def test_compute_velocity_current_only():
    # 1 m/s current to North (0 degrees)
    u, v, comps = compute_velocity(10.0, 80.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0)
    # v should be positive (North), u should be 0
    assert abs(u) < 1e-5
    assert v > 0
    assert comps["current_kts"] > 0
    assert comps["windage_kts"] == 0.0
    assert comps["stokes_kts"] == 0.0

def test_compute_velocity_wind_only():
    # 10 m/s wind to East (90 degrees), with waves (stokes)
    u, v, comps = compute_velocity(10.0, 80.0, 0.0, 0.0, 0.0, 10.0, 90.0, 2.0)
    # u should be positive (East), v should be 0
    assert u > 0
    assert abs(v) < 1e-5
    assert comps["current_kts"] == 0.0
    assert comps["windage_kts"] > 0
    assert comps["stokes_kts"] > 0

def test_invalid_velocity_input():
    with pytest.raises(ValueError):
        compute_velocity(float('nan'), 80.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0)

def test_predict_drift_basic():
    res = predict_drift(10.0, 80.0, 6, 1.0, 45.0, 10.0, 45.0, 1.0)
    assert res["simulation_status"] == "SUCCESS"
    assert "drift_components" in res
    assert len(res["predictions"]) == 3 # T+1, T+3, T+6
    
    p1 = res["predictions"][0]
    assert p1["horizon_hours"] == 1
    assert "lat" in p1["position"]
    assert "lon" in p1["position"]
    assert p1["uncertainty_radius_nm"] > 0

def test_predict_drift_invalid_horizon():
    with pytest.raises(ValueError):
        predict_drift(10.0, 80.0, -5, 1.0, 45.0, 10.0, 45.0, 1.0)

def test_generate_search_cone():
    res = predict_drift(10.0, 80.0, 3, 1.0, 45.0, 10.0, 45.0, 1.0)
    geojson = generate_search_cone(res["predictions"])
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 2 # T+1, T+3

def test_calculate_drift_prediction_tool():
    # Tool output
    res = calculate_drift_prediction.invoke({
        "incident_id": "TEST-123",
        "lkp_lat": 10.0,
        "lkp_lon": 80.0,
        "hours": 6
    })
    
    assert "error" not in res
    assert res["source"] == "SARProvider (MOCK-SARPhysics)"
    
    data = res["data"]
    assert data["incident_id"] == "TEST-123"
    assert "sar_prediction" in data
    
    sar_res = data["sar_prediction"]
    assert sar_res["simulation_status"] == "SUCCESS"
    assert len(sar_res["predictions"]) == 3
