import json
import os
import math
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from .base import (
    WeatherProvider,
    OceanProvider,
    EOProvider,
    GeospatialProvider,
    MarineDataProvider
)
from models import (
    GeoPoint,
    WeatherSnapshot,
    GeofenceCheckResult,
    GeofenceZone,
    ZoneType,
    WindData,
    WaveData,
    CurrentData
)

def load_fixture(path: str) -> Dict[str, Any]:
    base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "demo")
    full_path = os.path.join(base_dir, path)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def closest_scenario(lat: float, lon: float, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not scenarios:
        return {}
    
    best = scenarios[0]
    best_dist = float('inf')
    
    for s in scenarios:
        dist = math.hypot(s.get('lat', 0) - lat, s.get('lon', 0) - lon)
        if dist < best_dist:
            best_dist = dist
            best = s
            
    return best

class DemoWeatherProvider(WeatherProvider):
    def __init__(self):
        data = load_fixture(os.path.join("weather", "weather.json"))
        self.scenarios = data.get("weather_scenarios", [])
        
    async def get_weather_forecast(self, lat: float, lon: float) -> WeatherSnapshot:
        scenario = closest_scenario(lat, lon, self.scenarios)
        return WeatherSnapshot(
            position=GeoPoint(lat=lat, lon=lon),
            wind=WindData(
                speed_ms=scenario.get("wind_speed_ms", 5.0),
                direction_deg=scenario.get("wind_dir_deg", 180.0),
                source="MOCK-IMD"
            ),
            current=CurrentData(
                speed_ms=0.5,
                direction_deg=90.0,
                source="MOCK-INCOIS"
            ),
            wave=WaveData(
                significant_height_m=scenario.get("wave_height_m", 1.0),
                source="MOCK-INCOIS"
            ),
            is_simulated=True
        )
        
    async def get_wind(self, lat: float, lon: float) -> WindData:
        scenario = closest_scenario(lat, lon, self.scenarios)
        return WindData(
            speed_ms=scenario.get("wind_speed_ms", 5.0),
            direction_deg=scenario.get("wind_dir_deg", 180.0),
            source="MOCK-IMD"
        )
        
    async def get_wave_height(self, lat: float, lon: float) -> WaveData:
        scenario = closest_scenario(lat, lon, self.scenarios)
        return WaveData(
            significant_height_m=scenario.get("wave_height_m", 1.0),
            source="MOCK-INCOIS"
        )
        
    async def get_rainfall(self, lat: float, lon: float) -> Dict[str, Any]:
        scenario = closest_scenario(lat, lon, self.scenarios)
        return {
            "rainfall_mm": scenario.get("rainfall_mm", 0.0),
            "source": "MOCK-IMD",
            "is_simulated": True
        }
        
    async def get_cyclone_alerts(self, lat: float, lon: float) -> List[Dict[str, Any]]:
        scenario = closest_scenario(lat, lon, self.scenarios)
        alerts = scenario.get("alerts", [])
        return [{"alert": a, "source": "MOCK-IMD", "is_simulated": True} for a in alerts if "CYCLONE" in a]
        
    async def get_marine_advisories(self, lat: float, lon: float) -> List[Dict[str, Any]]:
        scenario = closest_scenario(lat, lon, self.scenarios)
        alerts = scenario.get("alerts", [])
        return [{"alert": a, "source": "MOCK-IMD", "is_simulated": True} for a in alerts]

class DemoOceanProvider(OceanProvider):
    def __init__(self):
        data = load_fixture(os.path.join("ocean", "currents.json"))
        self.scenarios = data.get("ocean_scenarios", [])
        
    async def get_ocean_conditions(self, lat: float, lon: float, timestamp: Optional[datetime] = None) -> CurrentData:
        scenario = closest_scenario(lat, lon, self.scenarios)
        return CurrentData(
            speed_ms=scenario.get("current_speed_ms", 0.5),
            direction_deg=scenario.get("current_dir_deg", 90.0),
            source="MOCK-INCOIS"
        )
        
    async def get_sea_state(self, lat: float, lon: float) -> Dict[str, Any]:
        scenario = closest_scenario(lat, lon, self.scenarios)
        return {
            "sea_temp_c": scenario.get("sea_temp_c", 28.0),
            "source": "MOCK-INCOIS",
            "is_simulated": True
        }
        
    async def get_tides(self, lat: float, lon: float) -> Dict[str, Any]:
        return {
            "tide_level_m": 1.2,
            "source": "MOCK-INCOIS",
            "is_simulated": True
        }

class DemoEOProvider(EOProvider):
    def __init__(self):
        data = load_fixture(os.path.join("eo", "pfz.json"))
        self.pfz_zones = data.get("pfz_zones", [])
        
    async def get_pfZ(self, lat: float, lon: float) -> Dict[str, Any]:
        # Return the nearest PFZ and all PFZs
        if not self.pfz_zones:
            return {"has_pfz": False, "is_simulated": True, "source": "MOCK-Bhoonidhi"}
            
        nearest = closest_scenario(lat, lon, self.pfz_zones)
        return {
            "has_pfz": True,
            "nearest": nearest,
            "all_zones": self.pfz_zones,
            "is_simulated": True,
            "source": "MOCK-Bhoonidhi"
        }
        
    async def get_chlorophyll(self, lat: float, lon: float) -> Dict[str, Any]:
        nearest = closest_scenario(lat, lon, self.pfz_zones)
        return {
            "chlorophyll_mgl": nearest.get("chlorophyll_mgl", 0.5),
            "is_simulated": True,
            "source": "MOCK-Bhoonidhi"
        }
        
    async def get_sst(self, lat: float, lon: float) -> Dict[str, Any]:
        nearest = closest_scenario(lat, lon, self.pfz_zones)
        return {
            "sst_c": nearest.get("sst_c", 28.0),
            "is_simulated": True,
            "source": "MOCK-Bhoonidhi"
        }

class DemoGeospatialProvider(GeospatialProvider):
    def __init__(self):
        data = load_fixture(os.path.join("geospatial", "zones.json"))
        self.zones = data.get("zones", [])
        
    async def check_geofence_violations(self, vessel_id: str) -> GeofenceCheckResult:
        from shapely.geometry import shape, Point
        
        if not self.zones:
            return GeofenceCheckResult(
                position=GeoPoint(lat=10, lon=80),
                in_zone=False,
                approaching_zone=False
            )
            
        # Using a mock vessel position if not provided, or ideally we'd pass it.
        # But this function only receives vessel_id. Wait, GeofenceCheckResult requires position.
        # In a real system, we look up vessel's LKP. Here we just mock one near IMBL.
        vessel_point = Point(79.4, 9.4)
        
        nearest_zone = None
        min_dist_deg = float('inf')
        in_zone = False
        
        for z in self.zones:
            if "geometry" in z:
                geom = shape(z["geometry"])
                dist = geom.distance(vessel_point)
                if dist < min_dist_deg:
                    min_dist_deg = dist
                    nearest_zone = z
                    in_zone = geom.contains(vessel_point)
                    
        # Rough conversion: 1 degree approx 60 NM
        dist_nm = min_dist_deg * 60.0
        
        approaching = False
        alert_msg = None
        if nearest_zone:
            buffer = nearest_zone.get("alert_buffer_nm", 5.0)
            if dist_nm <= buffer and not in_zone:
                approaching = True
                alert_msg = f"Approaching {nearest_zone.get('name')}"
            elif in_zone:
                alert_msg = f"Inside {nearest_zone.get('name')}"
                
            return GeofenceCheckResult(
                position=GeoPoint(lat=vessel_point.y, lon=vessel_point.x),
                in_zone=in_zone,
                approaching_zone=approaching,
                nearest_zone=GeofenceZone(
                    id=nearest_zone.get("id", "00000000-0000-0000-0000-000000000000"),
                    name=nearest_zone.get("name", "Unknown"),
                    zone_type=ZoneType(nearest_zone.get("zone_type", "IMBL")),
                    alert_buffer_nm=nearest_zone.get("alert_buffer_nm", 5.0)
                ),
                distance_nm=dist_nm,
                alert_message=alert_msg
            )
            
        return GeofenceCheckResult(
            position=GeoPoint(lat=vessel_point.y, lon=vessel_point.x),
            in_zone=False,
            approaching_zone=False
        )

    async def get_nearby_zones(self, lat: float, lon: float, radius_nm: float = 10.0) -> List[Dict[str, Any]]:
        from shapely.geometry import shape, Point
        
        nearby = []
        point = Point(lon, lat) # Shapely uses (x,y) -> (lon, lat)
        
        for z in self.zones:
            if "geometry" in z:
                geom = shape(z["geometry"])
                # 1 degree is roughly 60 nm
                dist_nm = geom.distance(point) * 60.0
                
                if dist_nm <= radius_nm:
                    # Include it
                    z_out = dict(z)
                    z_out["distance_nm"] = dist_nm
                    z_out["in_zone"] = geom.contains(point)
                    # Exclude heavy geometry for API response
                    if "geometry" in z_out:
                        del z_out["geometry"]
                    nearby.append(z_out)
                    
        nearby.sort(key=lambda x: x["distance_nm"])
        return nearby

    async def get_spatial_context(self, lat: float, lon: float) -> Dict[str, Any]:
        from packages.geospatial.h3_utils import point_to_h3, is_valid_coordinate
        
        if not is_valid_coordinate(lat, lon):
            return {"error": "Invalid coordinates"}
            
        h3_cell = point_to_h3(lat, lon, resolution=9)
        nearby_zones = await self.get_nearby_zones(lat, lon, radius_nm=15.0)
        
        in_zones = [z for z in nearby_zones if z.get("in_zone")]
        
        return {
            "lat": lat,
            "lon": lon,
            "h3_cell": h3_cell,
            "in_zones": in_zones,
            "nearby_zones": nearby_zones,
            "is_simulated": True,
            "source": "MOCK-GeospatialEngine"
        }

class DemoMarineDataProvider(MarineDataProvider):
    def __init__(self):
        self.weather = DemoWeatherProvider()
        self.ocean = DemoOceanProvider()
        self.eo = DemoEOProvider()
        
    async def get_marine_conditions(self, lat: float, lon: float) -> Dict[str, Any]:
        w = await self.weather.get_wind(lat, lon)
        o = await self.ocean.get_ocean_conditions(lat, lon)
        pfz = await self.eo.get_pfZ(lat, lon)
        
        return {
            "wind": w.model_dump(),
            "current": o.model_dump(),
            "pfz": pfz,
            "is_simulated": True,
            "source": "MOCK-MarineData"
        }
