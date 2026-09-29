"""
ORCA — SAR Physics Engine
Deterministic RK4-based drift prediction.
"""
from typing import List, Dict, Any
import math

class GeoPoint:
    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 3440.065 # nautical miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def compute_velocity(lat: float, lon: float, t_hours: float, current_speed_ms: float, current_dir_deg: float, wind_speed_ms: float, wind_dir_deg: float, wave_height_m: float = 0.0, leeway_pct: float = 0.03):
    """
    Compute total velocity vector in knots.
    current_speed_ms: m/s
    wind_speed_ms: m/s
    wave_height_m: m
    Returns (u_total, v_total, components_dict)
    """
    if any(math.isnan(x) or math.isinf(x) for x in [lat, lon, t_hours, current_speed_ms, current_dir_deg, wind_speed_ms, wind_dir_deg, wave_height_m]):
        raise ValueError("Invalid numerical input to compute_velocity")

    ms_to_kts = 1.94384
    
    # Ocean Current (Current usually goes TO direction in this mock, matching wind)
    u_c = current_speed_ms * ms_to_kts * math.sin(math.radians(current_dir_deg))
    v_c = current_speed_ms * ms_to_kts * math.cos(math.radians(current_dir_deg))
    
    # Wind leeway (approx 3% of wind speed)
    u_w = wind_speed_ms * ms_to_kts * leeway_pct * math.sin(math.radians(wind_dir_deg))
    v_w = wind_speed_ms * ms_to_kts * leeway_pct * math.cos(math.radians(wind_dir_deg))
    
    # Stokes drift (approx 1.5% of wind speed or based on wave height, here simple mock)
    # Direction roughly matches wind. Speed approx 1% of wind speed if waves > 0
    stokes_speed = (0.01 * wind_speed_ms) if wave_height_m > 0 else 0.0
    u_s = stokes_speed * ms_to_kts * math.sin(math.radians(wind_dir_deg))
    v_s = stokes_speed * ms_to_kts * math.cos(math.radians(wind_dir_deg))
    
    u_total = u_c + u_w + u_s
    v_total = v_c + v_w + v_s
    
    components = {
        "current_kts": math.sqrt(u_c**2 + v_c**2),
        "windage_kts": math.sqrt(u_w**2 + v_w**2),
        "stokes_kts": math.sqrt(u_s**2 + v_s**2),
        "total_kts": math.sqrt(u_total**2 + v_total**2)
    }
    
    return u_total, v_total, components

def rk4_step(lat: float, lon: float, t_hours: float, dt_hours: float, current_speed_ms: float, current_dir_deg: float, wind_speed_ms: float, wind_dir_deg: float, wave_height_m: float):
    """
    Take an RK4 step.
    Since environmental fields are static in this mock, k1=k2=k3=k4, but the geographic projection changes with latitude.
    """
    def get_derivatives(cur_lat, cur_lon, cur_t):
        u_kts, v_kts, _ = compute_velocity(cur_lat, cur_lon, cur_t, current_speed_ms, current_dir_deg, wind_speed_ms, wind_dir_deg, wave_height_m)
        dlat = v_kts / 60.0
        # Protect against polar singularity
        cos_lat = math.cos(math.radians(cur_lat))
        if abs(cos_lat) < 1e-4:
            cos_lat = 1e-4
        dlon = u_kts / (60.0 * cos_lat)
        return dlat, dlon

    # k1
    dlat1, dlon1 = get_derivatives(lat, lon, t_hours)
    
    # k2
    dlat2, dlon2 = get_derivatives(lat + 0.5 * dt_hours * dlat1, lon + 0.5 * dt_hours * dlon1, t_hours + 0.5 * dt_hours)
    
    # k3
    dlat3, dlon3 = get_derivatives(lat + 0.5 * dt_hours * dlat2, lon + 0.5 * dt_hours * dlon2, t_hours + 0.5 * dt_hours)
    
    # k4
    dlat4, dlon4 = get_derivatives(lat + dt_hours * dlat3, lon + dt_hours * dlon3, t_hours + dt_hours)
    
    next_lat = lat + (dt_hours / 6.0) * (dlat1 + 2 * dlat2 + 2 * dlat3 + dlat4)
    next_lon = lon + (dt_hours / 6.0) * (dlon1 + 2 * dlon2 + 2 * dlon3 + dlon4)
    
    return next_lat, next_lon

def predict_drift(start_lat: float, start_lon: float, hours: int, current_speed_ms: float, current_dir_deg: float, wind_speed_ms: float, wind_dir_deg: float, wave_height_m: float = 0.0) -> Dict[str, Any]:
    """
    Run the SAR drift model. Returns structured predictions including T+1, T+3, T+6.
    """
    if hours < 0:
        raise ValueError("Prediction horizon must be non-negative.")
        
    dt = 0.25 # 15 minute steps for better resolution
    t = 0.0
    
    lat = start_lat
    lon = start_lon
    
    predictions = []
    
    # Get initial components
    _, _, initial_components = compute_velocity(lat, lon, 0, current_speed_ms, current_dir_deg, wind_speed_ms, wind_dir_deg, wave_height_m)
    
    # Keep track of targets
    targets = [1, 3, 6]
    if hours not in targets and hours > 0:
        targets.append(hours)
    targets.sort()
    
    for target_hr in targets:
        if target_hr > hours:
            break
            
        while t < target_hr - 1e-5: # Floating point safety
            step_size = min(dt, target_hr - t)
            lat, lon = rk4_step(lat, lon, t, step_size, current_speed_ms, current_dir_deg, wind_speed_ms, wind_dir_deg, wave_height_m)
            t += step_size
            
        # Expanded uncertainty model: Base error + cumulative drift error
        # Assuming 5% error on drift speed + 0.5nm base
        uncertainty = 0.5 + (0.05 * initial_components["total_kts"] * target_hr)
        
        predictions.append({
            "horizon_hours": int(target_hr),
            "position": {
                "lat": lat,
                "lon": lon
            },
            "uncertainty_radius_nm": round(uncertainty, 2)
        })
            
    return {
        "initial_position": {"lat": start_lat, "lon": start_lon},
        "environmental_inputs": {
            "current_speed_ms": current_speed_ms,
            "current_dir_deg": current_dir_deg,
            "wind_speed_ms": wind_speed_ms,
            "wind_dir_deg": wind_dir_deg,
            "wave_height_m": wave_height_m
        },
        "drift_components": initial_components,
        "predictions": predictions,
        "simulation_status": "SUCCESS",
        "is_simulated": True
    }

def generate_search_cone(predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate GeoJSON for the search area.
    """
    features = []
    for p in predictions:
        features.append({
            "type": "Feature",
            "properties": {
                "horizon_hours": p["horizon_hours"],
                "uncertainty_radius_nm": p["uncertainty_radius_nm"]
            },
            "geometry": {
                "type": "Point",
                "coordinates": [p["position"]["lon"], p["position"]["lat"]]
            }
        })
        
    return {
        "type": "FeatureCollection",
        "features": features
    }
