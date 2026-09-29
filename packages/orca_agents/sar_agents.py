import asyncio
from typing import Dict, Any, List
from .models import SARPlanningContext, SARAgentResult

class SARPlanningAgent:
    @staticmethod
    async def execute(context: SARPlanningContext) -> SARAgentResult:
        """Analyze the SAR task, prepare execution plan."""
        return SARAgentResult(
            agent="SARPlanningAgent",
            status="success",
            data={
                "incident_id": context.incident_id,
                "plan": [
                    "Fetch Environment Data",
                    "Fetch Geospatial Context",
                    "Calculate SAR Drift",
                    "Synthesize Risk",
                    "Formulate Tactical Comms"
                ]
            }
        )

class EnvironmentAgent:
    @staticmethod
    async def execute(context: SARPlanningContext) -> SARAgentResult:
        """Fetch wind/current/wave data for the SAR location."""
        try:
            # Reusing existing providers
            from packages.marine_data import get_providers
            _, weather_provider, ocean_provider, _, _ = get_providers()
            w = await weather_provider.get_weather_forecast(context.lat, context.lon)
            o = await ocean_provider.get_sea_state(context.lat, context.lon)
            
            evidence = []
            
            # Wind Evidence
            evidence.append({
                "source": getattr(w.wind, "source", "Unknown"),
                "agent": "EnvironmentAgent",
                "tool": "weather_provider",
                "summary": f"Wind: {w.wind.speed_ms} m/s",
                "confidence": 0.9,
                "is_simulated": getattr(w, "is_simulated", True),
                "data": {"wind_speed_ms": w.wind.speed_ms, "wind_dir_deg": w.wind.direction_deg}
            })
            
            # Current Evidence
            evidence.append({
                "source": getattr(w.current, "source", "Unknown"),
                "agent": "EnvironmentAgent",
                "tool": "ocean_provider",
                "summary": f"Current: {w.current.speed_ms} m/s",
                "confidence": 0.85,
                "is_simulated": getattr(w, "is_simulated", True),
                "data": {"current_speed_ms": w.current.speed_ms, "current_dir_deg": w.current.direction_deg}
            })

            return SARAgentResult(
                agent="EnvironmentAgent",
                status="success",
                data={
                    "wind_speed_ms": w.wind.speed_ms,
                    "wind_dir_deg": w.wind.direction_deg,
                    "current_speed_ms": w.current.speed_ms,
                    "current_dir_deg": w.current.direction_deg,
                    "wave_height_m": w.wave.significant_height_m,
                    "sea_temp_c": o.get("sea_temp_c", 28.5) if isinstance(o, dict) else getattr(o, "sea_temp_c", 28.5)
                },
                evidence=evidence
            )
        except Exception as e:
            return SARAgentResult(
                agent="EnvironmentAgent",
                status="error",
                errors=[str(e)]
            )

class GeospatialAgent:
    @staticmethod
    async def execute(context: SARPlanningContext) -> SARAgentResult:
        """Identify zones, constraints, and boundaries near the incident."""
        try:
            from packages.marine_data import get_providers
            _, _, _, _, geo_provider = get_providers()
            geo_ctx = await geo_provider.get_spatial_context(context.lat, context.lon)
            
            evidence = []
            
            # Geospatial Evidence
            is_sim = geo_ctx.get("is_simulated", True) if isinstance(geo_ctx, dict) else getattr(geo_ctx, "is_simulated", True)
            
            evidence.append({
                "source": "GeoProvider",
                "agent": "GeospatialAgent",
                "tool": "geo_provider",
                "summary": f"Identified {len(geo_ctx.get('nearest_zones', [])) if isinstance(geo_ctx, dict) else len(getattr(geo_ctx, 'nearest_zones', []))} nearby zones.",
                "confidence": 0.95,
                "is_simulated": is_sim,
                "data": {"nearest_zones_count": len(geo_ctx.get('nearest_zones', [])) if isinstance(geo_ctx, dict) else len(getattr(geo_ctx, 'nearest_zones', []))}
            })

            return SARAgentResult(
                agent="GeospatialAgent",
                status="success",
                data=geo_ctx,
                evidence=evidence
            )
        except Exception as e:
            return SARAgentResult(
                agent="GeospatialAgent",
                status="error",
                errors=[str(e)]
            )

class SARPhysicsAgent:
    @staticmethod
    async def execute(context: SARPlanningContext, env_data: Dict[str, Any]) -> SARAgentResult:
        """Invoke Phase 9 SAR engine to calculate drift."""
        try:
            from packages.sar_physics.rk4 import predict_drift, generate_search_cone
            current_speed = env_data.get("current_speed_ms", 0.5)
            current_dir = env_data.get("current_dir_deg", 90.0)
            wind_speed = env_data.get("wind_speed_ms", 10.0)
            wind_dir = env_data.get("wind_dir_deg", 180.0)
            wave_height = env_data.get("wave_height_m", 1.5)
            
            # Predict for 6 hours
            res = predict_drift(context.lat, context.lon, 6, current_speed, current_dir, wind_speed, wind_dir, wave_height)
            
            # Search area cone
            cone = generate_search_cone(res["predictions"])
            
            return SARAgentResult(
                agent="SARPhysicsAgent",
                status="success",
                data={
                    "predictions": res["predictions"],
                    "search_areas": cone
                }
            )
        except Exception as e:
            return SARAgentResult(
                agent="SARPhysicsAgent",
                status="error",
                errors=[str(e)]
            )

class RiskAgent:
    @staticmethod
    async def execute(context: SARPlanningContext, env_data: Dict[str, Any], geo_data: Dict[str, Any], sar_data: Dict[str, Any]) -> SARAgentResult:
        """Combine specialist outputs into risk findings."""
        risks = []
        warnings = []
        
        # Environmental risks
        if env_data.get("wave_height_m", 0) > 2.0:
            risks.append(f"High wave heights ({env_data.get('wave_height_m')}m) may hamper rescue.")
        if env_data.get("wind_speed_ms", 0) > 15.0:
            risks.append(f"Strong winds ({env_data.get('wind_speed_ms')}m/s) detected.")
            
        # Geospatial risks
        if geo_data.get("in_zones"):
            zones = [z.get("name") for z in geo_data.get("in_zones", []) if z.get("zone_type") in ("IMBL", "RESTRICTED", "HAZARD")]
            if zones:
                risks.append(f"Incident inside restricted/hazardous zones: {', '.join(zones)}.")
                
        if not risks:
            risks.append("No critical environmental or geospatial risks identified.")
            
        return SARAgentResult(
            agent="RiskAgent",
            status="success",
            data={"risks": risks},
            warnings=warnings
        )

class TacticalCommsAgent:
    @staticmethod
    async def execute(context: SARPlanningContext, risk_data: Dict[str, Any], sar_data: Dict[str, Any]) -> SARAgentResult:
        """Formulate operational communication summary."""
        risks = risk_data.get("risks", [])
        risk_str = " | ".join(risks) if risks else "Standard Operation"
        
        preds = sar_data.get("predictions", [])
        if preds:
            final_p = preds[-1]
            drift_str = f"Drift heading to {final_p['position']['lat']:.4f}, {final_p['position']['lon']:.4f} in {final_p['horizon_hours']}h."
        else:
            drift_str = "No drift data available."
            
        message = f"MAYDAY RELAY: Vessel {context.vessel_id or 'UNKNOWN'} in distress at {context.lat:.4f}, {context.lon:.4f}. {drift_str} Risks: {risk_str}"
        
        return SARAgentResult(
            agent="TacticalCommsAgent",
            status="success",
            data={
                "message": message,
                "recipients": ["COAST_GUARD", "NEARBY_VESSELS"]
            }
        )
