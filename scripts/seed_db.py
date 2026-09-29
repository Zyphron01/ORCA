"""
ORCA — Demo Data Seeder
=====================================
Seeds the database with realistic demo vessels, incidents,
and geofence zones for local development and demo.

ALL data is clearly labelled as simulated/demo.
Run: python scripts/seed_db.py
"""

from __future__ import annotations

import asyncio
import sys
import os
import uuid
from datetime import datetime, timedelta

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "shared-types"))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text

# Load settings
from core.settings import settings
from core.db_models import Base, VesselORM, IncidentORM, GeofenceZoneORM, WeatherSnapshotORM
from models import IncidentType, IncidentStatus, VesselType, ZoneType


# ============================================================
# Demo Vessels (Indian fishing vessel names and regions)
# ============================================================

DEMO_VESSELS = [
    {
        "id": uuid.UUID("11111111-0000-0000-0000-000000000001"),
        "mmsi": "419000001",
        "name": "MFV Saraswati",
        "owner_name": "Ramu Nayak",
        "vessel_type": VesselType.FISHING_ARTISANAL,
        "transponder_id": "DATSG-TN-001",
        "lat": 12.5167,
        "lon": 80.1833,
        "heading": 245.0,
        "speed_kts": 4.2,
    },
    {
        "id": uuid.UUID("11111111-0000-0000-0000-000000000002"),
        "mmsi": "419000002",
        "name": "MFV Lakshmi Devi",
        "owner_name": "Krishnamurthy P.",
        "vessel_type": VesselType.FISHING_MECHANISED,
        "transponder_id": "DATSG-TN-002",
        "lat": 13.1000,
        "lon": 80.2833,
        "heading": 180.0,
        "speed_kts": 6.0,
    },
    {
        "id": uuid.UUID("11111111-0000-0000-0000-000000000003"),
        "mmsi": "419000003",
        "name": "MFV Durga Mata",
        "owner_name": "Suresh Kamath",
        "vessel_type": VesselType.FISHING_ARTISANAL,
        "transponder_id": "NABH-KA-003",
        "lat": 13.8540,
        "lon": 74.7500,
        "heading": 270.0,
        "speed_kts": 3.5,
    },
    {
        "id": uuid.UUID("11111111-0000-0000-0000-000000000004"),
        "mmsi": "419000004",
        "name": "MFV Sagar Shanti",
        "owner_name": "Abdul Rahman",
        "vessel_type": VesselType.FISHING_MECHANISED,
        "transponder_id": "NABH-KL-004",
        "lat": 10.9167,
        "lon": 76.2833,
        "heading": 310.0,
        "speed_kts": 7.1,
    },
    {
        "id": uuid.UUID("11111111-0000-0000-0000-000000000005"),
        "mmsi": "419000005",
        "name": "ICGS Vikram",
        "owner_name": "Indian Coast Guard",
        "vessel_type": VesselType.COAST_GUARD,
        "transponder_id": "ICG-OPS-005",
        "lat": 13.0827,
        "lon": 80.2707,
        "heading": 180.0,
        "speed_kts": 12.0,
    },
]


# ============================================================
# Demo Incidents
# ============================================================

DEMO_INCIDENTS = [
    {
        "id": uuid.UUID("22222222-0000-0000-0000-000000000001"),
        "vessel_id": uuid.UUID("11111111-0000-0000-0000-000000000001"),
        "incident_type": IncidentType.SOS,
        "status": IncidentStatus.ACTIVE,
        "lkp_lat": 12.5,
        "lkp_lon": 80.8,
        "lkp_time": datetime.utcnow() - timedelta(hours=2),
        "description": "[DEMO] Fishing Vessel Engine Failure: Fishing vessel reports engine failure and requests immediate assistance.",
    },
    {
        "id": uuid.UUID("22222222-0000-0000-0000-000000000002"),
        "vessel_id": uuid.UUID("11111111-0000-0000-0000-000000000002"),
        "incident_type": IncidentType.COMMS_LOSS,
        "status": IncidentStatus.ACTIVE,
        "lkp_lat": 13.0,
        "lkp_lon": 81.2,
        "lkp_time": datetime.utcnow() - timedelta(hours=1),
        "description": "[DEMO] Vessel Communication Lost: Fishing vessel stopped responding to scheduled communication checks. Last known position available.",
    },
    {
        "id": uuid.UUID("22222222-0000-0000-0000-000000000003"),
        "vessel_id": uuid.UUID("11111111-0000-0000-0000-000000000003"),
        "incident_type": IncidentType.SOS,  # Map to SOS to avoid enum errors
        "status": IncidentStatus.ACTIVE,
        "lkp_lat": 13.3,
        "lkp_lon": 80.6,
        "lkp_time": datetime.utcnow() - timedelta(minutes=30),
        "description": "[DEMO] Medical Emergency Onboard: Crew member reported a medical emergency and requested coastal authority assistance.",
    },
]


# ============================================================
# Demo Geofence Zones (approximate — for demo purposes only)
# ============================================================

DEMO_GEOFENCES = [
    {
        "id": uuid.UUID("33333333-0000-0000-0000-000000000001"),
        "name": "India-Sri Lanka Maritime Boundary (IMBL) — Demo",
        "zone_type": ZoneType.IMBL,
        "description": "[DEMO DATA] Approximate IMBL between India and Sri Lanka. Not for navigation.",
        "authority": "Ministry of External Affairs",
        "alert_buffer_nm": 2.0,
        # Approximate polygon — demo only, NOT authoritative
        "wkt": "MULTIPOLYGON(((79.0 9.5, 80.5 9.5, 80.5 8.0, 79.0 8.0, 79.0 9.5)))",
    },
    {
        "id": uuid.UUID("33333333-0000-0000-0000-000000000002"),
        "name": "Gulf of Mannar Marine National Park (MPA) — Demo",
        "zone_type": ZoneType.MPA,
        "description": "[DEMO DATA] Marine Protected Area. Trawling prohibited.",
        "authority": "Ministry of Environment",
        "alert_buffer_nm": 1.0,
        "wkt": "MULTIPOLYGON(((78.1 9.0, 79.2 9.0, 79.2 8.5, 78.1 8.5, 78.1 9.0)))",
    },
]


# ============================================================
# Seeder
# ============================================================

async def seed(db: AsyncSession) -> None:
    print("ORCA Demo Data Seeder")
    print("=" * 50)
    print("ALL DATA IS SIMULATED/DEMO - NOT REAL")
    print("=" * 50)

    # Vessels
    for v_data in DEMO_VESSELS:
        existing = await db.get(VesselORM, v_data["id"])
        if existing is None:
            vessel = VesselORM(
                id=v_data["id"],
                mmsi=v_data["mmsi"],
                name=v_data["name"],
                owner_name=v_data["owner_name"],
                vessel_type=v_data["vessel_type"],
                transponder_id=v_data["transponder_id"],
                lat=v_data["lat"],
                lon=v_data["lon"],
                heading=v_data["heading"],
                speed_kts=v_data["speed_kts"],
                last_seen_at=datetime.utcnow(),
                is_active=True,
            )
            db.add(vessel)
            print(f"  [OK] Vessel: {v_data['name']}")
        else:
            print(f"  [SKIP] Vessel already exists: {v_data['name']}")

    # Incidents
    for inc_data in DEMO_INCIDENTS:
        existing = await db.get(IncidentORM, inc_data["id"])
        if existing is None:
            incident = IncidentORM(**inc_data)
            db.add(incident)
            print(f"  [OK] Incident: {inc_data['incident_type']} for vessel {inc_data['vessel_id']}")

    # Geofence Zones (PostGIS ST_GeomFromText)
    for zone_data in DEMO_GEOFENCES:
        result = await db.execute(
            text("SELECT id FROM geofence_zones WHERE id = :id"),
            {"id": str(zone_data["id"])},
        )
        if result.scalar_one_or_none() is None:
            await db.execute(
                text("""
                    INSERT INTO geofence_zones (id, name, zone_type, boundary, alert_buffer_nm, description, authority)
                    VALUES (
                        :id, :name, CAST(:zone_type AS zone_type_enum),
                        ST_Multi(ST_GeomFromText(:wkt, 4326)),
                        :buffer, :description, :authority
                    )
                """),
                {
                    "id": str(zone_data["id"]),
                    "name": zone_data["name"],
                    "zone_type": zone_data["zone_type"].value,
                    "wkt": zone_data["wkt"],
                    "buffer": zone_data["alert_buffer_nm"],
                    "description": zone_data["description"],
                    "authority": zone_data["authority"],
                },
            )
            print(f"  [OK] Geofence: {zone_data['name']}")

    await db.commit()
    print("\n[OK] Seed complete!")


async def main() -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        await seed(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
