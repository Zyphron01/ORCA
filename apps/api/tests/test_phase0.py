"""
ORCA — Phase 0 Tests
===================================
Tests for shared types, settings, and basic API contracts.
Run: pytest apps/api/tests/ -v
"""

from __future__ import annotations

import sys
import os
import uuid
from datetime import datetime

import pytest

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "shared-types"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestGeoPoint:
    """Test coordinate validation."""

    def test_valid_coordinate(self):
        from models import GeoPoint
        p = GeoPoint(lat=13.08, lon=80.27)
        assert p.lat == pytest.approx(13.08)
        assert p.lon == pytest.approx(80.27)

    def test_invalid_lat_too_high(self):
        from models import GeoPoint
        import pydantic
        with pytest.raises((pydantic.ValidationError, ValueError)):
            GeoPoint(lat=91.0, lon=80.0)

    def test_invalid_lat_too_low(self):
        from models import GeoPoint
        import pydantic
        with pytest.raises((pydantic.ValidationError, ValueError)):
            GeoPoint(lat=-91.0, lon=80.0)

    def test_invalid_lon_too_high(self):
        from models import GeoPoint
        import pydantic
        with pytest.raises((pydantic.ValidationError, ValueError)):
            GeoPoint(lat=13.0, lon=181.0)

    def test_indian_ocean_coordinate(self):
        from models import GeoPoint
        # Bay of Bengal
        p = GeoPoint(lat=12.5167, lon=80.1833)
        assert p.lat is not None
        assert p.lon is not None

    def test_coordinate_rounding(self):
        from models import GeoPoint
        p = GeoPoint(lat=13.0827123456789, lon=80.2707987654321)
        # Should round to 6 decimal places
        assert len(str(p.lat).split(".")[-1]) <= 6


class TestVesselModels:
    """Test vessel data models."""

    def test_vessel_create_basic(self):
        from models import VesselCreate, VesselType
        v = VesselCreate(name="MFV Saraswati", vessel_type=VesselType.FISHING_ARTISANAL)
        assert v.name == "MFV Saraswati"

    def test_vessel_requires_name(self):
        from models import VesselCreate
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            VesselCreate(name="")  # Too short

    def test_vessel_with_mmsi(self):
        from models import VesselCreate
        v = VesselCreate(name="ICGS Vikram", mmsi="419000001")
        assert v.mmsi == "419000001"


class TestIncidentModels:
    """Test incident data models."""

    def test_incident_create(self):
        from models import IncidentCreate, IncidentType, GeoPoint
        inc = IncidentCreate(
            vessel_id=uuid.uuid4(),
            incident_type=IncidentType.SOS,
            lkp=GeoPoint(lat=12.5, lon=80.2),
        )
        assert inc.incident_type == IncidentType.SOS
        assert inc.lkp.lat == pytest.approx(12.5)


class TestORCAModels:
    """Test ORCA session models."""

    def test_query_request_valid(self):
        from models import ORCAQueryRequest
        req = ORCAQueryRequest(message="What is the sea condition near Chennai coast?")
        assert req.message.startswith("What")
        assert req.session_id is None

    def test_query_request_with_session(self):
        from models import ORCAQueryRequest
        sid = uuid.uuid4()
        req = ORCAQueryRequest(
            message="Continue previous analysis",
            session_id=sid,
        )
        assert req.session_id == sid

    def test_query_too_long(self):
        from models import ORCAQueryRequest
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            ORCAQueryRequest(message="x" * 4001)

    def test_evidence_item(self):
        from models import EvidenceItem
        e = EvidenceItem(
            source="MOCK-INCOIS",
            agent="HydroMeteoAgent",
            tool="get_currents",
            summary="Surface current: 0.8 m/s at 245°",
            is_simulated=True,
            confidence=0.9,
        )
        assert e.is_simulated is True
        assert e.confidence == pytest.approx(0.9)


class TestDriftModels:
    """Test drift prediction models."""

    def test_force_breakdown_valid(self):
        from models import DriftForceBreakdown
        fb = DriftForceBreakdown(current_pct=62.0, wind_pct=26.0, stokes_pct=12.0)
        assert fb.current_pct + fb.wind_pct + fb.stokes_pct == pytest.approx(100.0)

    def test_force_breakdown_invalid_sum(self):
        from models import DriftForceBreakdown
        import pydantic
        with pytest.raises((pydantic.ValidationError, ValueError)):
            DriftForceBreakdown(current_pct=50.0, wind_pct=50.0, stokes_pct=20.0)

    def test_drift_point(self):
        from models import DriftPoint, DriftHorizon, DriftForceBreakdown, GeoPoint
        dp = DriftPoint(
            horizon_h=DriftHorizon.T1,
            position=GeoPoint(lat=12.6, lon=80.1),
            force_breakdown=DriftForceBreakdown(
                current_pct=62.0, wind_pct=26.0, stokes_pct=12.0
            ),
            uncertainty_radius_nm=2.5,
        )
        assert dp.horizon_h == 1
        assert dp.uncertainty_radius_nm == pytest.approx(2.5)


class TestHealthModel:
    """Test health check model."""

    def test_health_default(self):
        from models import HealthStatus
        h = HealthStatus()
        assert h.status == "ok"
        assert h.db == "ok"
        assert h.redis == "ok"
        assert h.phase.startswith("Phase")

    def test_health_degraded(self):
        from models import HealthStatus
        h = HealthStatus(status="degraded", db="error")
        assert h.status == "degraded"
        assert h.db == "error"


class TestSettings:
    """Test settings configuration."""

    def test_settings_loads(self):
        from core.settings import settings
        assert settings.version == "0.1.0"
        assert settings.app_port == 8000

    def test_demo_mode_default(self):
        from core.settings import settings
        assert settings.enable_demo_mode is True

    def test_real_apis_disabled_by_default(self):
        from core.settings import settings
        assert settings.enable_real_incois is False
        assert settings.enable_real_imd is False
        assert settings.enable_real_bhoonidhi is False


class TestGeofenceModels:
    """Test geofence models."""

    def test_geofence_check_request(self):
        from models import GeofenceCheckRequest, GeoPoint
        req = GeofenceCheckRequest(position=GeoPoint(lat=9.2, lon=79.5))
        assert req.position.lat == pytest.approx(9.2)

    def test_geofence_result(self):
        from models import GeofenceCheckResult, GeoPoint
        result = GeofenceCheckResult(
            position=GeoPoint(lat=9.2, lon=79.5),
            in_zone=True,
            approaching_zone=False,
        )
        assert result.in_zone is True


class TestSOSModels:
    """Test SOS workflow models."""

    def test_sos_trigger(self):
        from models import SOSTrigger, GeoPoint
        trigger = SOSTrigger(
            vessel_id=uuid.uuid4(),
            position=GeoPoint(lat=12.5, lon=80.2),
            trigger_type="MANUAL",
            crew_count=4,
        )
        assert trigger.trigger_type == "MANUAL"
        assert trigger.crew_count == 4
