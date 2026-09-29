import pytest
import uuid
from httpx import AsyncClient
from main import app
from sqlalchemy.ext.asyncio import AsyncSession
from core.db_models import IncidentORM, VesselORM, DriftPredictionORM, ORCASessionORM, AgentTaskORM
from core.database import AsyncSessionLocal

@pytest.mark.asyncio
async def test_get_intelligence_report():
    async with AsyncSessionLocal() as db_session:
        # Setup test data
        vessel = VesselORM(
            id=uuid.uuid4(),
            name="Report Test Vessel",
            vessel_type="FISHING_ARTISANAL"
        )
        db_session.add(vessel)
        await db_session.flush()
        
        incident_id = uuid.uuid4()
        session_id = uuid.uuid4()
        
        from datetime import datetime
        
        incident = IncidentORM(
            id=incident_id,
            vessel_id=vessel.id,
            incident_type="SOS",
            status="ACTIVE",
            lkp_lat=12.0,
            lkp_lon=80.0,
            lkp_time=datetime.utcnow(),
            orca_session_id=session_id
        )
        db_session.add(incident)
        await db_session.flush()
        
        # Add ORCA Session
        orca_session = ORCASessionORM(
            id=session_id,
            incident_id=incident_id,
            status="DONE"
        )
        db_session.add(orca_session)
        await db_session.flush()
        
        # Add agent trace
        agent_task = AgentTaskORM(
            id=uuid.uuid4(),
            session_id=session_id,
            agent_name="SARPhysicsAgent",
            tool_name="rk4_drift",
            status="DONE",
            input_payload={}
        )
        db_session.add(agent_task)
        
        # Add drift prediction
        drift = DriftPredictionORM(
            id=uuid.uuid4(),
            incident_id=incident_id,
            horizon_h=1,
            predicted_lat=12.1,
            predicted_lon=80.1
        )
        db_session.add(drift)
        await db_session.commit()

        import httpx
        from core.database import get_db
        
        async def override_get_db():
            yield db_session
            
        app.dependency_overrides[get_db] = override_get_db
        
        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/authority/incidents/{incident_id}/report")
            
        assert response.status_code == 200
        data = response.json()
        
        assert data["incident_id"] == str(incident_id)
        assert data["vessel_name"] == "Report Test Vessel"
        assert len(data["sar_predictions"]) == 1
        assert data["sar_predictions"][0]["horizon_h"] == 1
        assert len(data["agent_traces"]) == 1
        assert data["agent_traces"][0]["agent_name"] == "SARPhysicsAgent"
        
        # Cleanup
        app.dependency_overrides.pop(get_db, None)
