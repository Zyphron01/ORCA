import os
from typing import Tuple

from .providers.base import (
    MarineDataProvider,
    WeatherProvider,
    OceanProvider,
    EOProvider,
    GeospatialProvider
)
from .providers.demo import (
    DemoMarineDataProvider,
    DemoWeatherProvider,
    DemoOceanProvider,
    DemoEOProvider,
    DemoGeospatialProvider
)

def get_providers() -> Tuple[MarineDataProvider, WeatherProvider, OceanProvider, EOProvider, GeospatialProvider]:
    """Factory to get the correct providers based on DATA_MODE"""
    mode = os.getenv("DATA_MODE", "demo").lower()
    
    if mode == "demo":
        return (
            DemoMarineDataProvider(),
            DemoWeatherProvider(),
            DemoOceanProvider(),
            DemoEOProvider(),
            DemoGeospatialProvider()
        )
    elif mode == "live":
        raise NotImplementedError("Live data providers are not yet implemented in Phase 2.")
    else:
        raise ValueError(f"Unsupported DATA_MODE: {mode}. Use 'demo' or 'live'.")
