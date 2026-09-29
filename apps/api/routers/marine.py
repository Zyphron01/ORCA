from fastapi import APIRouter
import sys
import os

router = APIRouter(prefix="/api/v1/marine", tags=["marine"])

@router.get("/status")
async def get_marine_status(lat: float, lon: float):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages"))
    from orca_core.tools import get_marine_weather
    
    res = get_marine_weather.invoke({
        "lat": lat,
        "lon": lon
    })
    
    return {"status": "success", "weather": res}
