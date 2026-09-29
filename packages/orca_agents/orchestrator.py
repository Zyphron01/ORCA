import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List

from .models import SARPlanningContext, SARAgentResult, SARFinalResult
from .sar_agents import (
    SARPlanningAgent,
    EnvironmentAgent,
    GeospatialAgent,
    SARPhysicsAgent,
    RiskAgent,
    TacticalCommsAgent
)

class SAROrchestrator:
    @staticmethod
    async def execute_sar_workflow(context: SARPlanningContext) -> SARFinalResult:
        """
        Executes the multi-agent SAR orchestration workflow.
        Follows the dependency graph:
        Plan -> (Env + Geo) -> Physics -> Risk -> Comms -> Synthesis
        """
        trace = []
        
        def add_trace(res: SARAgentResult):
            trace.append({
                "agent": res.agent,
                "status": res.status,
                "summary": f"Executed with status {res.status}",
                "errors": res.errors
            })
            
        # 1. Planning
        plan_res = await SARPlanningAgent.execute(context)
        add_trace(plan_res)
        
        # 2. Parallel: Environment & Geospatial
        env_task = asyncio.create_task(EnvironmentAgent.execute(context))
        geo_task = asyncio.create_task(GeospatialAgent.execute(context))
        
        env_res, geo_res = await asyncio.gather(env_task, geo_task)
        add_trace(env_res)
        add_trace(geo_res)
        
        env_data = env_res.data if env_res.status == "success" else {}
        geo_data = geo_res.data if geo_res.status == "success" else {}
        
        # 3. Physics (Depends on Env)
        sar_res = await SARPhysicsAgent.execute(context, env_data)
        add_trace(sar_res)
        sar_data = sar_res.data if sar_res.status == "success" else {}
        
        # 4. Risk Synthesis (Depends on Env, Geo, Physics)
        risk_res = await RiskAgent.execute(context, env_data, geo_data, sar_data)
        add_trace(risk_res)
        risk_data = risk_res.data if risk_res.status == "success" else {}
        
        # 5. Tactical Communications (Depends on Risk, Physics)
        comms_res = await TacticalCommsAgent.execute(context, risk_data, sar_data)
        add_trace(comms_res)
        comms_data = comms_res.data if comms_res.status == "success" else {}
        
        # Aggregate evidence
        all_evidence = []
        for res in [plan_res, env_res, geo_res, sar_res, risk_res, comms_res]:
            if hasattr(res, "evidence") and res.evidence:
                all_evidence.extend(res.evidence)
                
        # 6. Final Synthesis
        return SARFinalResult(
            incident_id=context.incident_id,
            sar_predictions=sar_data.get("predictions", []),
            search_areas=sar_data.get("search_areas", []),
            environment=env_data,
            geospatial=geo_data,
            risks=risk_data.get("risks", []),
            communications=comms_data,
            agent_trace=trace,
            evidence=all_evidence,
            is_simulated=True
        )
