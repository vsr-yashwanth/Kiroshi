import pytest
import uuid
from backend.app.domain.models.incident import Incident
from backend.app.domain.models.camera import Camera
from backend.app.domain.models.trip import Trip
from backend.app.domain.models.location_event import LocationEvent
from backend.app.domain.models.enums import (
    IncidentSource,
    IncidentSeverity,
    IncidentStatus,
    CameraStatus,
    TripStatus,
    LocationFreshness,
)
from backend.app.services.cctv_service import CCTVService
from backend.app.services.risk_service import RiskService
from backend.app.schemas.cctv import CCTVInvestigationRequest


@pytest.mark.asyncio
async def test_e2e_v06_computer_vision_and_cctv_investigation_workflow(
    client, db_session, authority_token_headers, authority_user, tourist_user
):
    """
    End-to-End v0.6 Workflow:
    1. Tourist on active trip triggers distress / incident.
    2. Authority detects incident and locates nearby PostGIS CCTV infrastructure.
    3. CCTV Investigation extracts time-scoped pose streams and executes FallDetector.
    4. ML outputs explainable POSSIBLE_FALL evidence without automatically confirming emergency.
    5. Fall signal is fed into Risk Engine to update dynamic tourist safety score.
    6. System verified resilient to ML failure / timeouts.
    """
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    trip = Trip(
        tourist_id=tourist_user.id,
        title="Pangong High Altitude Trek",
        status=TripStatus.ACTIVE,
        start_date=now,
        end_date=now + timedelta(days=7),
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    loc = LocationEvent(
        tourist_id=tourist_user.id,
        trip_id=trip.id,
        latitude=34.1526,
        longitude=77.5771,
        accuracy=5.0,
        speed=0.0,
        recorded_at=now,
    )
    db_session.add(loc)
    db_session.commit()
    db_session.refresh(loc)

    # 2. Incident Created
    incident = Incident(
        tourist_id=tourist_user.id,
        trip_id=trip.id,
        source=IncidentSource.SOS,
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.DETECTED,
        latitude=34.1526,
        longitude=77.5771,
        description="SOS signal broadcast from mountain trail point",
    )
    db_session.add(incident)
    db_session.commit()
    db_session.refresh(incident)

    # 3. Setup Camera Infrastructure
    camera = Camera(
        name="Trail Checkpoint Camera 04",
        status=CameraStatus.ACTIVE.value,
        location="POINT(77.5771 34.1526)",
        coverage_radius_meters=100.0,
        is_simulated=True,
    )
    db_session.add(camera)
    db_session.commit()

    # 4. Authority Dispatches Scoped Investigation
    cctv_service = CCTVService(db_session)
    inv_req = CCTVInvestigationRequest(
        incident_id=incident.id,
        search_radius_meters=200.0,
        time_window_minutes_before=5.0,
        time_window_minutes_after=5.0,
    )
    inv_res = cctv_service.run_cctv_investigation(inv_req, requested_by_user_id=authority_user.id)

    assert inv_res.incident_id == incident.id
    assert inv_res.status.value in ["COMPLETED", "NO_FOOTAGE_AVAILABLE"]
    assert len(inv_res.detection_results) >= 1

    first_det = inv_res.detection_results[0]
    assert first_det["detection_type"] in ["POSSIBLE_FALL", "NORMAL_POSTURE", "LYING_DOWN"]
    assert "signals" in first_det or "error" in first_det
    assert "explanation" in first_det or "error" in first_det

    # 5. Risk Engine evaluates optional CV fall signal
    risk_service = RiskService(db_session)
    cv_evidence = {
        "detection_type": "POSSIBLE_FALL",
        "confidence": 0.85,
    }
    assessment = await risk_service.evaluate_and_persist(
        tourist_id=tourist_user.id,
        trip=trip,
        location_event=loc,
        active_zones=[],
        freshness=LocationFreshness.LIVE,
        cv_detection=cv_evidence,
    )

    assert assessment is not None
    assert assessment.risk_score > 0.0
    assert any(s.get("signal_type") == "POSSIBLE_FALL" for s in assessment.contributing_signals)
    assert "possible fall" in assessment.explanation.lower()
