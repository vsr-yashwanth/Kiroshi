import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.domain.models.user import User
from backend.app.domain.models.trip import Trip
from backend.app.domain.models.incident import Incident
from backend.app.domain.models.enums import UserRole, TripStatus, IncidentStatus, IncidentSeverity
from backend.app.core.security import create_access_token


def test_sync_sos_event_success_and_idempotency(client: TestClient, db_session: Session):
    """
    Verifies that offline SOS sync creates an incident and returns SYNCED,
    and repeated submissions with the same local_event_id return DUPLICATE
    without creating duplicate incidents.
    """
    tourist = User(
        email="sync_tourist_1@kiroshi.org",
        hashed_password="hash",
        full_name="Sync Tourist One",
        role=UserRole.TOURIST,
        is_active=True,
    )
    db_session.add(tourist)
    db_session.commit()
    db_session.refresh(tourist)

    token = create_access_token(subject=str(tourist.id), role=tourist.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    local_event_id = f"local-sos-{uuid.uuid4()}"
    event_timestamp = datetime.now(timezone.utc).isoformat()

    batch_payload = {
        "events": [
            {
                "local_event_id": local_event_id,
                "event_type": "SOS_EVENT",
                "timestamp": event_timestamp,
                "payload": {
                    "latitude": 35.6585,
                    "longitude": 139.7454,
                    "accuracy": 12.5,
                    "notes": "Offline emergency SOS test",
                },
                "retry_count": 0,
            }
        ]
    }

    # First submission: should succeed and create incident
    resp1 = client.post("/api/v1/sync/events", json=batch_payload, headers=headers)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["synced_count"] == 1
    assert data1["duplicate_count"] == 0
    assert data1["failed_count"] == 0
    assert len(data1["results"]) == 1
    res1 = data1["results"][0]
    assert res1["local_event_id"] == local_event_id
    assert res1["status"] == "SYNCED"
    assert res1["server_id"] is not None

    incident_id = uuid.UUID(res1["server_id"])
    incident = db_session.query(Incident).filter(Incident.id == incident_id).first()
    assert incident is not None
    assert incident.severity == IncidentSeverity.CRITICAL
    assert incident.status == IncidentStatus.DETECTED
    assert incident.tourist_id == tourist.id

    # Second submission (network retry / duplicate): MUST be caught by server-side idempotency
    resp2 = client.post("/api/v1/sync/events", json=batch_payload, headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["synced_count"] == 0
    assert data2["duplicate_count"] == 1
    assert data2["failed_count"] == 0
    assert data2["results"][0]["status"] == "DUPLICATE"
    assert data2["results"][0]["server_id"] == str(incident_id)

    # Verify only ONE incident was created in total for this tourist
    incidents = db_session.query(Incident).filter(Incident.tourist_id == tourist.id).all()
    assert len(incidents) == 1


def test_sync_location_events_and_late_arrival(client: TestClient, db_session: Session):
    """
    Verifies offline location batch ingestion, timestamp preservation for late-arriving points,
    and freshness calculation.
    """
    tourist = User(
        email="sync_loc_tourist@kiroshi.org",
        hashed_password="hash",
        full_name="Location Tourist",
        role=UserRole.TOURIST,
        is_active=True,
    )
    db_session.add(tourist)
    db_session.commit()
    db_session.refresh(tourist)

    trip = Trip(
        tourist_id=tourist.id,
        title="Offline Active Trip",
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=3),
        status=TripStatus.ACTIVE,
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    token = create_access_token(subject=str(tourist.id), role=tourist.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    # Simulate locations recorded 15 minutes ago offline
    past_time = datetime.now(timezone.utc) - timedelta(minutes=15)
    loc_key = f"loc-{uuid.uuid4()}"

    batch_payload = {
        "events": [
            {
                "local_event_id": loc_key,
                "event_type": "LOCATION_EVENT",
                "timestamp": past_time.isoformat(),
                "payload": {
                    "trip_id": str(trip.id),
                    "latitude": 35.6812,
                    "longitude": 139.7671,
                    "accuracy": 8.0,
                    "altitude": 25.0,
                    "speed": 1.4,
                    "heading": 90.0,
                    "recorded_at": past_time.isoformat(),
                },
                "retry_count": 1,
            }
        ]
    }

    resp = client.post("/api/v1/sync/events", json=batch_payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["synced_count"] == 1
    assert data["results"][0]["status"] == "SYNCED"


def test_sync_trip_lifecycle_conflict_handling(client: TestClient, db_session: Session):
    """
    Verifies conflict resolution policies:
    - START on already completed trip -> CONFLICT (SERVER_WINS)
    - STOP on already completed trip -> idempotent SYNCED
    """
    tourist = User(
        email="trip_conflict_tourist@kiroshi.org",
        hashed_password="hash",
        full_name="Trip Conflict Tourist",
        role=UserRole.TOURIST,
        is_active=True,
    )
    db_session.add(tourist)
    db_session.commit()
    db_session.refresh(tourist)

    # Create a trip that is already COMPLETED on server
    completed_trip = Trip(
        tourist_id=tourist.id,
        title="Completed Trip",
        start_date=datetime.now(timezone.utc) - timedelta(days=2),
        end_date=datetime.now(timezone.utc) - timedelta(days=1),
        status=TripStatus.COMPLETED,
    )
    db_session.add(completed_trip)
    db_session.commit()
    db_session.refresh(completed_trip)

    token = create_access_token(subject=str(tourist.id), role=tourist.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    # Client attempts to send START for already completed trip
    batch_payload = {
        "events": [
            {
                "local_event_id": f"trip-start-{uuid.uuid4()}",
                "event_type": "TRIP_UPDATE",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "trip_id": str(completed_trip.id),
                    "action": "START",
                },
            }
        ]
    }

    resp = client.post("/api/v1/sync/events", json=batch_payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["failed_count"] == 1
    res = data["results"][0]
    assert res["status"] == "CONFLICT"
    assert res["conflict_details"]["resolution"] == "SERVER_WINS"

    # Client attempts to send STOP for already completed trip -> Idempotent SYNCED
    stop_payload = {
        "events": [
            {
                "local_event_id": f"trip-stop-{uuid.uuid4()}",
                "event_type": "TRIP_UPDATE",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "trip_id": str(completed_trip.id),
                    "action": "STOP",
                },
            }
        ]
    }
    stop_resp = client.post("/api/v1/sync/events", json=stop_payload, headers=headers)
    assert stop_resp.status_code == 200
    stop_data = stop_resp.json()
    assert stop_data["synced_count"] == 1
    assert stop_data["results"][0]["status"] == "SYNCED"


def test_sync_partial_batch_tolerance(client: TestClient, db_session: Session):
    """
    Verifies that a failure in one queued event (e.g. invalid trip ID)
    does NOT abort or roll back valid events (e.g. valid SOS) in the same batch.
    """
    tourist = User(
        email="partial_sync_tourist@kiroshi.org",
        hashed_password="hash",
        full_name="Partial Sync Tourist",
        role=UserRole.TOURIST,
        is_active=True,
    )
    db_session.add(tourist)
    db_session.commit()
    db_session.refresh(tourist)

    token = create_access_token(subject=str(tourist.id), role=tourist.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    sos_key = f"sos-partial-{uuid.uuid4()}"
    invalid_loc_key = f"loc-invalid-{uuid.uuid4()}"

    batch_payload = {
        "events": [
            {
                "local_event_id": sos_key,
                "event_type": "SOS_EVENT",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "latitude": 35.6585,
                    "longitude": 139.7454,
                    "accuracy": 10.0,
                    "notes": "Emergency in partial batch",
                },
            },
            {
                "local_event_id": invalid_loc_key,
                "event_type": "LOCATION_EVENT",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "trip_id": str(uuid.uuid4()),  # Non-existent trip
                    "latitude": 35.6812,
                    "longitude": 139.7671,
                    "accuracy": 5.0,
                },
            },
        ]
    }

    resp = client.post("/api/v1/sync/events", json=batch_payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["synced_count"] == 1
    assert data["failed_count"] == 1

    results_map = {r["local_event_id"]: r for r in data["results"]}
    assert results_map[sos_key]["status"] == "SYNCED"
    assert results_map[invalid_loc_key]["status"] == "REJECTED"

    # Verify that the SOS incident was indeed committed to the database
    incident_id = uuid.UUID(results_map[sos_key]["server_id"])
    incident = db_session.query(Incident).filter(Incident.id == incident_id).first()
    assert incident is not None
