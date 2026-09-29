"""
ORCA — Tools and Mock Adapters
"""
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from datetime import datetime, timezone
import sys
import os
import asyncio
import concurrent.futures
import math

# Add packages to path if not there
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from marine_data import get_providers

def run_sync(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
        
    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(1) as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 3440.065 # Earth radius in nautical miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class WeatherForecastInput(BaseModel):
    lat: float = Field(..., description="Latitude of the location")
    lon: float = Field(..., description="Longitude of the location")

@tool(args_schema=WeatherForecastInput)
def fetch_weather_forecast(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch weather and ocean forecast from WeatherProvider.
    Use this when you need wind, wave, or current data.
    """
    _, weather_provider, ocean_provider, _, _ = get_providers()
    w = run_sync(weather_provider.get_weather_forecast(lat, lon))
    o = run_sync(ocean_provider.get_sea_state(lat, lon))
    
    return {
        "source": "WeatherProvider (MOCK-INCOIS)",
        "agent": "HydroMeteo",
        "tool": "fetch_weather_forecast",
        "evidence_context": {
            "domain": "weather",
            "purpose": "weather_assessment"
        },
        "is_simulated": w.is_simulated,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "lat": lat,
            "lon": lon,
            "wind_speed_ms": w.wind.speed_ms,
            "wind_dir_deg": w.wind.direction_deg,
            "current_speed_ms": w.current.speed_ms,
            "current_dir_deg": w.current.direction_deg,
            "wave_height_m": w.wave.significant_height_m,
            "sea_temp_c": o.get("sea_temp_c", 28.5)
        },
        "summary": f"Weather at {lat}, {lon}: Wind {w.wind.speed_ms}m/s, Wave {w.wave.significant_height_m}m.",
        "evidence": [
            {
                "type": "weather",
                "asset_id": "weather_demo_001",
                "value": w.wind.speed_ms,
                "unit": "m/s",
                "summary": f"Wind speed is {w.wind.speed_ms} m/s.",
                "is_simulated": w.is_simulated,
                "confidence": 0.95
            },
            {
                "type": "wave",
                "asset_id": "wave_demo_001",
                "value": w.wave.significant_height_m,
                "unit": "m",
                "summary": f"Significant wave height is {w.wave.significant_height_m} m.",
                "is_simulated": w.is_simulated,
                "confidence": 0.92
            }
        ]
    }

class DriftPredictionInput(BaseModel):
    incident_id: str = Field(..., description="Unique ID of the incident")
    lkp_lat: float = Field(..., description="Last known position latitude")
    lkp_lon: float = Field(..., description="Last known position longitude")
    hours: int = Field(6, description="Hours to predict drift for")

@tool(args_schema=DriftPredictionInput)
def calculate_drift_prediction(incident_id: str, lkp_lat: float, lkp_lon: float, hours: int = 6) -> Dict[str, Any]:
    """
    Calculate drift prediction (RK4) using SAR engine.
    Use this when a vessel is in distress and you need to predict where they will drift over time.
    """
    from packages.sar_physics.rk4 import predict_drift
    
    _, weather_provider, ocean_provider, _, _ = get_providers()
    w = run_sync(weather_provider.get_weather_forecast(lkp_lat, lkp_lon))
    o = run_sync(ocean_provider.get_sea_state(lkp_lat, lkp_lon))
    
    current_speed = w.current.speed_ms
    current_dir = w.current.direction_deg
    wind_speed = w.wind.speed_ms
    wind_dir = w.wind.direction_deg
    wave_height = w.wave.significant_height_m
    
    res = predict_drift(lkp_lat, lkp_lon, hours, current_speed, current_dir, wind_speed, wind_dir, wave_height)
    
    # Extract the final requested horizon for the summary
    final_pred = res["predictions"][-1]
    
    return {
        "source": "SARProvider (MOCK-SARPhysics)",
        "agent": "SARPhysics",
        "tool": "calculate_drift_prediction",
        "evidence_context": {
            "domain": "sar",
            "purpose": "sar_assessment"
        },
        "is_simulated": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "incident_id": incident_id,
            "sar_prediction": res
        },
        "summary": f"Predicted drift over {final_pred['horizon_hours']}h from {lkp_lat},{lkp_lon} places vessel near {final_pred['position']['lat']:.4f},{final_pred['position']['lon']:.4f} with search radius {final_pred['uncertainty_radius_nm']}nm.",
        "evidence": [
            {
                "type": "sar",
                "asset_id": "sar_drift_001",
                "value": final_pred['uncertainty_radius_nm'],
                "unit": "NM",
                "summary": f"Predicted uncertainty radius is {final_pred['uncertainty_radius_nm']} NM.",
                "is_simulated": True,
                "confidence": 0.88
            }
        ]
    }

class GeofenceViolationInput(BaseModel):
    vessel_id: str = Field(None, description="MMSI or unique ID of the vessel")
    lat: float = Field(None, description="Latitude to check")
    lon: float = Field(None, description="Longitude to check")

@tool(args_schema=GeofenceViolationInput)
def check_geofence_violations(vessel_id: str = None, lat: float = None, lon: float = None) -> Dict[str, Any]:
    """
    Check if a location or vessel is violating any geofences (IMBL, MPA, etc.).
    """
    _, _, _, _, geo_provider = get_providers()
    if vessel_id:
        res = run_sync(geo_provider.check_geofence_violations(vessel_id))
    else:
        res = run_sync(geo_provider.check_geofence_violations("dummy-vessel-for-loc"))
        if lat is not None and lon is not None:
            res.position.lat = lat
            res.position.lon = lon
            dist = haversine(lat, lon, 10.0, 80.0)
            res.distance_nm = dist
            if dist < 5.0:
                res.in_zone = True
                res.approaching_zone = True
                res.alert_message = "IMBL Violation"
            elif dist < 15.0:
                res.in_zone = False
                res.approaching_zone = True
                res.alert_message = "Approaching IMBL boundary"
            else:
                res.in_zone = False
                res.approaching_zone = False
                res.alert_message = "Safe distance from IMBL"
    
    return {
        "source": "GeospatialProvider (MOCK-HazardSentry)",
        "agent": "HazardSentry",
        "tool": "check_geofence_violations",
        "evidence_context": {
            "domain": "route",
            "purpose": "route_safety"
        },
        "is_simulated": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "lat": lat or (res.position.lat if res.position else None),
            "lon": lon or (res.position.lon if res.position else None),
            "in_violation": res.in_zone,
            "approaching_zone": res.approaching_zone,
            "nearest_zone": res.nearest_zone.name if res.nearest_zone else "None",
            "distance_nm": res.distance_nm if res.distance_nm is not None else 999.0
        },
        "summary": res.alert_message or f"Safe from geofences.",
        "evidence": [
            {
                "type": "geofence",
                "asset_id": "geofence_demo_001",
                "value": res.distance_nm if res.distance_nm is not None else 999.0,
                "unit": "NM",
                "summary": f"Distance to nearest zone: {res.distance_nm:.1f} NM" if res.distance_nm is not None else "Safe distance.",
                "is_simulated": True,
                "confidence": 0.99
            }
        ]
    }

class PFZAdvisoryInput(BaseModel):
    lat: float = Field(..., description="Latitude of the user's location")
    lon: float = Field(..., description="Longitude of the user's location")

@tool(args_schema=PFZAdvisoryInput)
def check_pfz_advisory(lat: float, lon: float) -> Dict[str, Any]:
    """
    Check Potential Fishing Zone (PFZ) advisory. Returns all nearby PFZs sorted by distance.
    """
    _, _, _, eo_provider, _ = get_providers()
    res = run_sync(eo_provider.get_pfZ(lat, lon))
    
    zones = res.get("all_zones", [])
    
    enriched_zones = []
    for z in zones:
        z_lat = z.get("lat", 0.0)
        z_lon = z.get("lon", 0.0)
        dist = haversine(lat, lon, z_lat, z_lon)
        z_copy = dict(z)
        z_copy["distance_nm"] = dist
        enriched_zones.append(z_copy)
        
    enriched_zones.sort(key=lambda x: x["distance_nm"])
    
    nearest_dist = enriched_zones[0]['distance_nm'] if enriched_zones else None
    
    return {
        "source": "EOProvider (MOCK-Bhoonidhi)",
        "agent": "MarineEO",
        "tool": "check_pfz_advisory",
        "evidence_context": {
            "domain": "pfz",
            "purpose": "fishing_zone_recommendation"
        },
        "is_simulated": res.get("is_simulated", True),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "origin_lat": lat,
            "origin_lon": lon,
            "has_pfz": res.get("has_pfz", False),
            "pfz_zones": enriched_zones
        },
        "summary": f"Found {len(enriched_zones)} PFZs near {lat},{lon}. Nearest is {nearest_dist:.1f}nm away." if enriched_zones else "No PFZs found.",
        "evidence": [
            {
                "type": "pfz",
                "asset_id": "pfz_demo_001",
                "value": nearest_dist,
                "unit": "NM",
                "summary": f"Nearest PFZ distance: {nearest_dist:.1f} NM",
                "is_simulated": True,
                "confidence": 0.85
            },
            {
                "type": "sst",
                "asset_id": "sst_demo_001",
                "value": 29.5,
                "unit": "°C",
                "summary": "Sea Surface Temperature is optimal for fish aggregation.",
                "is_simulated": True,
                "confidence": 0.90
            },
            {
                "type": "chlorophyll",
                "asset_id": "chl_demo_001",
                "value": 0.6,
                "unit": "mg/m³",
                "summary": "Chlorophyll concentration indicates nutrient-rich waters.",
                "is_simulated": True,
                "confidence": 0.80
            }
        ] if enriched_zones else []
    }

class RouteSafetyInput(BaseModel):
    start_lat: float = Field(..., description="Start latitude")
    start_lon: float = Field(..., description="Start longitude")
    end_lat: float = Field(..., description="End latitude")
    end_lon: float = Field(..., description="End longitude")
    speed_kts: float = Field(10.0, description="Vessel speed in knots")

@tool(args_schema=RouteSafetyInput)
def evaluate_route_safety(start_lat: float, start_lon: float, end_lat: float, end_lon: float, speed_kts: float = 10.0) -> Dict[str, Any]:
    """
    Evaluate the safety of a route from start to end. 
    Segments the route, checks weather and geographic zones (IMBL, MPA) along the way, 
    and suggests alternative routes if the baseline is unsafe.
    """
    from packages.geospatial.h3_utils import calculate_bearing, is_valid_coordinate
    
    if not is_valid_coordinate(start_lat, start_lon) or not is_valid_coordinate(end_lat, end_lon):
        return {"error": "Invalid coordinates provided."}
        
    if start_lat == end_lat and start_lon == end_lon:
        return {"error": "Origin and destination cannot be identical."}
        
    dist_nm = haversine(start_lat, start_lon, end_lat, end_lon)
    bearing = calculate_bearing(start_lat, start_lon, end_lat, end_lon)
    eta_hours = dist_nm / speed_kts if speed_kts > 0 else 999.0
    
    _, weather_provider, ocean_provider, _, geo_provider = get_providers()
    
    # 1. Generate segments (e.g. check every 10nm or at least start, mid, end)
    num_segments = max(3, int(dist_nm / 10.0))
    waypoints = []
    
    for i in range(num_segments + 1):
        fraction = i / num_segments
        w_lat = start_lat + (end_lat - start_lat) * fraction
        w_lon = start_lon + (end_lon - start_lon) * fraction
        waypoints.append({"lat": w_lat, "lon": w_lon})
        
    def evaluate_route(wp_list):
        hazards = []
        restricted_areas = []
        safe = True
        
        # Evaluate end weather
        end_wp = wp_list[-1]
        w = run_sync(weather_provider.get_weather_forecast(end_wp["lat"], end_wp["lon"]))
        alerts = run_sync(weather_provider.get_marine_advisories(end_wp["lat"], end_wp["lon"]))
        
        if w.wind.speed_ms > 15.0:
            safe = False
            hazards.append(f"High wind speed ({w.wind.speed_ms}m/s)")
        if w.wave.significant_height_m > 2.5:
            safe = False
            hazards.append(f"High wave height ({w.wave.significant_height_m}m)")
        if alerts:
            hazards.extend([a.get("alert") for a in alerts])
            safe = False
            
        # Evaluate geospatial for each waypoint
        for wp in wp_list:
            ctx = run_sync(geo_provider.get_spatial_context(wp["lat"], wp["lon"]))
            if "in_zones" in ctx:
                for z in ctx["in_zones"]:
                    # Depending on zone type, we might mark unsafe
                    zt = z.get("zone_type", "")
                    z_name = z.get("name", "Unknown Zone")
                    if zt in ["IMBL", "RESTRICTED", "HAZARD"]:
                        safe = False
                        if z_name not in restricted_areas:
                            restricted_areas.append(z_name)
                    elif zt == "MPA":
                        if z_name not in restricted_areas:
                            restricted_areas.append(f"{z_name} (MPA - verify permissions)")
                            
        return {
            "is_safe": safe,
            "hazards": hazards,
            "restricted_areas": restricted_areas,
            "destination_wind_ms": w.wind.speed_ms,
            "destination_wave_m": w.wave.significant_height_m
        }

    # Evaluate baseline route
    base_eval = evaluate_route(waypoints)
    
    # 2. Generate Alternatives (Simple: offset mid-point by 0.1 deg lat/lon)
    alt_waypoints_1 = waypoints[:]
    mid_idx = len(waypoints) // 2
    alt_waypoints_1[mid_idx] = {"lat": waypoints[mid_idx]["lat"] + 0.1, "lon": waypoints[mid_idx]["lon"] + 0.1}
    alt_eval_1 = evaluate_route(alt_waypoints_1)
    
    alt_waypoints_2 = waypoints[:]
    alt_waypoints_2[mid_idx] = {"lat": waypoints[mid_idx]["lat"] - 0.1, "lon": waypoints[mid_idx]["lon"] - 0.1}
    alt_eval_2 = evaluate_route(alt_waypoints_2)
    
    alternatives = []
    if alt_eval_1["is_safe"] and not base_eval["is_safe"]:
        alternatives.append({"name": "Alternative 1 (North/East Detour)", "eval": alt_eval_1})
    if alt_eval_2["is_safe"] and not base_eval["is_safe"]:
        alternatives.append({"name": "Alternative 2 (South/West Detour)", "eval": alt_eval_2})
        
    risk_level = "LOW" if base_eval["is_safe"] else "HIGH"
    recommendation = "Proceed with caution." if base_eval["is_safe"] else "Route intersects hazards/zones. Consider alternatives."
    if base_eval["restricted_areas"]:
        reasons = [f"Intersects: {', '.join(base_eval['restricted_areas'])}"]
    else:
        reasons = ["No geospatial restrictions."]
    
    return {
        "source": "NavigationAgent (Synthesized)",
        "agent": "RouteAgent",
        "tool": "evaluate_route_safety",
        "is_simulated": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "route": waypoints,
            "distance_nm": dist_nm,
            "bearing_deg": bearing,
            "estimated_hours": eta_hours,
            "hazards": base_eval["hazards"],
            "restricted_areas": base_eval["restricted_areas"],
            "marine_conditions": {
                "wind_ms": base_eval["destination_wind_ms"],
                "wave_m": base_eval["destination_wave_m"]
            },
            "risk_level": risk_level,
            "recommendation": recommendation,
            "reasons": reasons,
            "alternatives": alternatives
        },
        "summary": f"Route is {risk_level} RISK. Distance: {dist_nm:.1f}nm. ETA: {eta_hours:.1f}h. Restricted: {', '.join(base_eval['restricted_areas']) if base_eval['restricted_areas'] else 'None'}.",
        "evidence": [
            {
                "type": "route",
                "asset_id": "route_demo_001",
                "value": dist_nm,
                "unit": "NM",
                "summary": f"Route evaluated over {dist_nm:.1f} NM.",
                "is_simulated": True,
                "confidence": 0.90
            }
        ]
    }

class CalculateDistanceInput(BaseModel):
    lat1: float = Field(..., description="Latitude 1")
    lon1: float = Field(..., description="Longitude 1")
    lat2: float = Field(..., description="Latitude 2")
    lon2: float = Field(..., description="Longitude 2")

@tool(args_schema=CalculateDistanceInput)
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> Dict[str, Any]:
    """
    Calculate the nautical distance between two points.
    """
    dist_nm = haversine(lat1, lon1, lat2, lon2)
    return {
        "source": "GeospatialUtils",
        "agent": "GeospatialAgent",
        "tool": "calculate_distance",
        "is_simulated": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "distance_nm": dist_nm
        },
        "summary": f"Distance is {dist_nm:.2f} nautical miles."
    }

class GeospatialContextInput(BaseModel):
    lat: float = Field(..., description="Latitude to check")
    lon: float = Field(..., description="Longitude to check")

@tool(args_schema=GeospatialContextInput)
def get_spatial_context(lat: float, lon: float) -> Dict[str, Any]:
    """
    Get multi-layer geospatial context for a specific location including H3 cell, 
    intersecting zones, and nearby zones (MPAs, restricted areas, IMBL).
    """
    _, _, _, _, geo_provider = get_providers()
    res = run_sync(geo_provider.get_spatial_context(lat, lon))
    
    if "error" in res:
        return res
        
    in_zones_str = ", ".join([z.get("name", "Unknown") for z in res.get("in_zones", [])])
    
    return {
        "source": "GeospatialProvider (MOCK-GeospatialEngine)",
        "agent": "GeospatialAgent",
        "tool": "get_spatial_context",
        "is_simulated": res.get("is_simulated", True),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": res,
        "summary": f"H3: {res.get('h3_cell')}. Inside: {in_zones_str or 'None'}. Nearby zones: {len(res.get('nearby_zones', []))}."
    }

class ManageEmergencyInput(BaseModel):
    action: str = Field(..., description="Action to perform: TRIGGER, CAPSIZE, CANCEL, RESCUE, STATUS")
    vessel_id: str = Field(None, description="Vessel UUID for TRIGGER")
    incident_id: str = Field(None, description="Incident UUID for state transitions")
    lat: float = Field(None, description="Latitude for TRIGGER")
    lon: float = Field(None, description="Longitude for TRIGGER")
    description: str = Field(None, description="Description of the emergency")

@tool(args_schema=ManageEmergencyInput)
def manage_emergency(action: str, vessel_id: str = None, incident_id: str = None, lat: float = None, lon: float = None, description: str = None) -> Dict[str, Any]:
    """
    Manage marine emergencies. Use this to TRIGGER an SOS, simulate a CAPSIZE, CANCEL an emergency, mark as RESCUE, or get STATUS.
    """
    import sys
    import os
    if os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "packages", "shared-types")) not in sys.path:
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "packages", "shared-types")))
    from models import IncidentStatus, IncidentType
    import uuid
    from datetime import datetime, timezone
    
    # We will use direct DB access or simulate if no DB is available.
    # To keep it robust without relying on FastAPI context, we just return the desired intent,
    # and the system can process it. Actually, ORCA tools execute in backend.
    
    try:
        from apps.api.core.database import async_session_maker
        from apps.api.core.db_models import IncidentORM
        from sqlalchemy import select
        has_db = True
    except ImportError:
        has_db = False
        
    async def _handle():
        if not has_db:
            return {"error": "Database not available"}
        async with async_session_maker() as db:
            if action.upper() == "TRIGGER":
                if not vessel_id or not lat or not lon:
                    return {"error": "Missing vessel_id, lat, or lon for TRIGGER"}
                new_id = uuid.uuid4()
                inc = IncidentORM(
                    id=new_id,
                    vessel_id=uuid.UUID(vessel_id),
                    incident_type="SOS",
                    status="ACTIVE",
                    lkp_lat=lat,
                    lkp_lon=lon,
                    lkp_time=datetime.utcnow(),
                    description=description or "Simulated via ORCA"
                )
                db.add(inc)
                await db.commit()
                return {"incident_id": str(new_id), "status": "ACTIVE", "type": "SOS"}
            
            if not incident_id:
                return {"error": "Missing incident_id"}
                
            result = await db.execute(select(IncidentORM).where(IncidentORM.id == uuid.UUID(incident_id)))
            inc = result.scalar_one_or_none()
            if not inc:
                return {"error": f"Incident {incident_id} not found"}
                
            if action.upper() == "STATUS":
                return {"incident_id": str(inc.id), "status": inc.status, "type": inc.incident_type, "lat": inc.lkp_lat, "lon": inc.lkp_lon}
                
            act = action.upper()
            if act == "CAPSIZE":
                inc.status = "CAPSIZED"
                inc.incident_type = "CAPSIZE"
            elif act == "CANCEL":
                inc.status = "CANCELLED"
            elif act == "RESCUE":
                inc.status = "RESCUED"
                
            await db.commit()
            return {"incident_id": str(inc.id), "status": inc.status, "type": inc.incident_type}

    if has_db:
        res = run_sync(_handle())
    else:
        res = {"status": "mocked", "action": action}

    return {
        "source": "EmergencySimulator",
        "agent": "SARPhysics",
        "tool": "manage_emergency",
        "is_simulated": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": res,
        "summary": f"Emergency action {action} processed."
    }

class RunSAROrchestrationInput(BaseModel):
    incident_id: str = Field(..., description="Unique ID of the incident to run SAR analysis for")
    vessel_id: str = Field(None, description="Vessel UUID if known")
    lat: float = Field(..., description="Latitude of incident")
    lon: float = Field(..., description="Longitude of incident")
    timestamp: str = Field(..., description="Timestamp of the incident in ISO format")

@tool(args_schema=RunSAROrchestrationInput)
def run_sar_orchestration(incident_id: str, lat: float, lon: float, timestamp: str, vessel_id: str = None) -> Dict[str, Any]:
    """
    Run a full multi-agent Search and Rescue orchestration (SAR).
    This delegates the task to the SAR Planning, Physics, Environment, Geospatial, Risk, and Tactical Comms agents.
    """
    import sys
    import os
    if os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "packages")) not in sys.path:
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "packages")))
        
    from packages.orca_agents.models import SARPlanningContext
    from packages.orca_agents.orchestrator import SAROrchestrator
    
    ctx = SARPlanningContext(
        incident_id=incident_id,
        vessel_id=vessel_id,
        lat=lat,
        lon=lon,
        timestamp=timestamp
    )
    
    res = run_sync(SAROrchestrator.execute_sar_workflow(ctx))
    
    return {
        "source": "SAROrchestrator",
        "agent": "SARPlanner",
        "tool": "run_sar_orchestration",
        "is_simulated": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": res.model_dump(),
        "summary": f"Multi-Agent SAR orchestration completed. {len(res.agent_trace)} agents executed. {len(res.risks)} risks identified."
    }

ORCA_TOOLS = [
    fetch_weather_forecast,
    calculate_drift_prediction,
    check_geofence_violations,
    check_pfz_advisory,
    evaluate_route_safety,
    calculate_distance,
    get_spatial_context,
    manage_emergency,
    run_sar_orchestration
]
