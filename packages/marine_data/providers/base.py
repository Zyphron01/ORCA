from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared-types"))

from models import (
    GeoPoint, 
    WeatherSnapshot, 
    GeofenceCheckResult,
    WindData,
    WaveData,
    CurrentData
)

class WeatherProvider(ABC):
    @abstractmethod
    async def get_weather_forecast(self, lat: float, lon: float) -> WeatherSnapshot:
        pass
        
    @abstractmethod
    async def get_wind(self, lat: float, lon: float) -> WindData:
        pass
        
    @abstractmethod
    async def get_wave_height(self, lat: float, lon: float) -> WaveData:
        pass
        
    @abstractmethod
    async def get_rainfall(self, lat: float, lon: float) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    async def get_cyclone_alerts(self, lat: float, lon: float) -> List[Dict[str, Any]]:
        pass
        
    @abstractmethod
    async def get_marine_advisories(self, lat: float, lon: float) -> List[Dict[str, Any]]:
        pass

class OceanProvider(ABC):
    @abstractmethod
    async def get_ocean_conditions(self, lat: float, lon: float, timestamp: Optional[datetime] = None) -> CurrentData:
        pass
        
    @abstractmethod
    async def get_sea_state(self, lat: float, lon: float) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    async def get_tides(self, lat: float, lon: float) -> Dict[str, Any]:
        pass

class EOProvider(ABC):
    @abstractmethod
    async def get_pfZ(self, lat: float, lon: float) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    async def get_chlorophyll(self, lat: float, lon: float) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    async def get_sst(self, lat: float, lon: float) -> Dict[str, Any]:
        pass

class GeospatialProvider(ABC):
    @abstractmethod
    async def check_geofence_violations(self, vessel_id: str) -> GeofenceCheckResult:
        pass

    @abstractmethod
    async def get_nearby_zones(self, lat: float, lon: float, radius_nm: float = 10.0) -> List[Dict[str, Any]]:
        pass
        
    @abstractmethod
    async def get_spatial_context(self, lat: float, lon: float) -> Dict[str, Any]:
        pass

class MarineDataProvider(ABC):
    """Facade for aggregating marine data"""
    @abstractmethod
    async def get_marine_conditions(self, lat: float, lon: float) -> Dict[str, Any]:
        pass
