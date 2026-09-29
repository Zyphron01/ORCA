from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
import os

router = APIRouter(prefix="/api/v1/route", tags=["route"])

class RouteRequest(BaseModel):
    vessel_id: str
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    speed_kts: Optional[float] = 10.0

@router.post("/evaluate")
async def evaluate_route(request: RouteRequest):
    # Import the Phase 8 tool
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages"))
    from orca_core.tools import evaluate_route_safety
    
    res = evaluate_route_safety.invoke({
        "start_lat": request.start_lat,
        "start_lon": request.start_lon,
        "end_lat": request.end_lat,
        "end_lon": request.end_lon,
        "speed_kts": request.speed_kts
    })
    
    return res
