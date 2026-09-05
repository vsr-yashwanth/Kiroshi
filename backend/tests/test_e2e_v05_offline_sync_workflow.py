import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.domain.models.user import User
from backend.app.domain.models.trip import Trip
from backend.app.domain.models.incident import Incident
from backend.app.domain.models.location_event import LocationEvent
from backend.app.domain.models.enums import (
    UserRole,
    TripStatus,
    IncidentStatus,
    IncidentSeverity,
    LocationFreshness,
)
from backend.app.core.security import create_access_token


def test_complete_v05_offline_first_safety_lifecycle(
    client: TestClient, db_session: Session
):
    """
    E2E Milestone Verification for KIROSHI v0.5 — Offline-First Safety (Phase 43).

    Simulates the exact real-world scenario:
    1. Tourist registers and starts a trip online.
    2. Network is lost -> Tourist continues moving offline.
    3. Location telemetry breadcrumbs are queued locally.
    4. Tourist encounters life-threatening hazard and activates emergency SOS offline.
    5. SOS is queued locally with unique idempotency key.
    6. Application process terminates (crash/kill simulation).
    7. Application restarts offline -> Persistent queue survives intact.
    8. Cellular connectivity is restored -> Single sync worker initiates controlled sync.
    9. Server receives batch, verifies timestamps, ingests locations, creates incident.
    10. Server sends acknowledgement -> Local client marks SOS as SENT.
    11. Network hiccup causes duplicate sync replay -> Server idempotently suppresses duplicate.
    12. Dispatch authority accesses incident console and verifies exactly ONE incident exists.
    """
    # 1. Setup: Tourist and Authority personnel
    tourist = User(
        email="offline_survivor@kiroshi.org",
        hashed_password="hash",
        full_name="Elena Rostova",
        role=UserRole.TOURIST,
        is_active=True,
    )
    authority = User(
        email="commander_v05@kiroshi.org",
        hashed_password="hash",
        full_name="Chief Inspector Kato",
        role=UserRole.AUTHORITY,
        is_active=True,
    )
    db_session.add_all([tourist, authority])
    db_session.commit()
    db_session.refresh(tourist)
    db_session.refresh(authority)

    tourist_token = create_access_token(
        subject=str(tourist.id), role=tourist.role.value
    )
    tourist_headers = {"Authorization": f"Bearer {tourist_token}"}

    authority_token = create_access_token(
        subject=str(authority.id), role=authority.role.value
    )
    authority_headers = {"Authorization": f"Bearer {authority_token}"}


    # Tourist starts trip online
    trip = Trip(
        tourist_id=tourist.id,
        title="Mount Fuji Northern Ridge Trek",
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=2),
        status=TripStatus.ACTIVE,
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    # 2. Network Disappears (Simulated on client)
    # 3. Tourist moves offline -> Local event queue accumulates items
    t0 = datetime.now(timezone.utc) - timedelta(minutes=20)
    t1 = datetime.now(timezone.utc) - timedelta(minutes=15)
    t2 = datetime.now(timezone.utc) - timedelta(minutes=5)  # SOS triggered

    loc_event_1_id = f"local-loc-1-{uuid.uuid4()}"
    loc_event_2_id = f"local-loc-2-{uuid.uuid4()}"
    sos_event_id = f"local-sos-life-{uuid.uuid4()}"

    simulated_offline_queue = [
        {
            "local_event_id": loc_event_1_id,
            "event_type": "LOCATION_EVENT",
            "timestamp": t0.isoformat(),
            "payload": {
                "trip_id": str(trip.id),
                "latitude": 35.3606,
                "longitude": 138.7274,
                "accuracy": 7.5,
                "altitude": 2800.0,
                "speed": 1.1,
                "heading": 45.0,
                "recorded_at": t0.isoformat(),
            },
            "retry_count": 0,
        },
        {
            "local_event_id": loc_event_2_id,
            "event_type": "LOCATION_EVENT",
            "timestamp": t1.isoformat(),
            "payload": {
                "trip_id": str(trip.id),
                "latitude": 35.3620,
                "longitude": 138.7290,
                "accuracy": 6.8,
                "altitude": 2950.0,
                "speed": 0.9,
                "heading": 50.0,
                "recorded_at": t1.isoformat(),
            },
            "retry_count": 0,
        },
        {
            "local_event_id": sos_event_id,
            "event_type": "SOS_EVENT",
            "timestamp": t2.isoformat(),
            "payload": {
                "trip_id": str(trip.id),
                "latitude": 35.3625,
                "longitude": 138.7300,
                "accuracy": 5.0,
                "notes": "Rockfall occurred, leg injured, freezing conditions.",
            },
            "retry_count": 0,
        },
    ]

    # 4. App termination and restart simulation:
    # In-memory transient state would be lost, but persisted queue is re-read.
    recovered_queue = list(simulated_offline_queue)

    # 5. Network Restored -> Single Sync Worker submits batch
    sync_resp = client.post(
        "/api/v1/sync/events",
        json={"events": recovered_queue},
        headers=tourist_headers,
    )
    assert sync_resp.status_code == 200
    sync_data = sync_resp.json()

    assert sync_data["synced_count"] == 3
    assert sync_data["duplicate_count"] == 0
    assert sync_data["failed_count"] == 0

    results_by_id = {r["local_event_id"]: r for r in sync_data["results"]}

    # Verify both locations were ingested
    assert results_by_id[loc_event_1_id]["status"] == "SYNCED"
    assert results_by_id[loc_event_2_id]["status"] == "SYNCED"

    # Verify SOS was acknowledged with authoritative server incident ID
    assert results_by_id[sos_event_id]["status"] == "SYNCED"
    incident_server_id = uuid.UUID(results_by_id[sos_event_id]["server_id"])

    # 6. Verify Incident on Database
    incident = (
        db_session.query(Incident).filter(Incident.id == incident_server_id).first()
    )
    assert incident is not None
    assert incident.severity == IncidentSeverity.CRITICAL
    assert incident.status == IncidentStatus.DETECTED
    assert incident.tourist_id == tourist.id
    assert incident.trip_id == trip.id
    assert "Rockfall" in incident.description

    # 7. Unstable Network Retry Simulation:
    # Client did not receive the ACK due to network timeout right after server processed,
    # so client sync engine retries the SOS event with the same local_event_id.
    duplicate_sync_resp = client.post(
        "/api/v1/sync/events",
        json={
            "events": [
                {
                    "local_event_id": sos_event_id,
                    "event_type": "SOS_EVENT",
                    "timestamp": t2.isoformat(),
                    "payload": {
                        "trip_id": str(trip.id),
                        "latitude": 35.3625,
                        "longitude": 138.7300,
                        "accuracy": 5.0,
                        "notes": "Rockfall occurred, leg injured, freezing conditions.",
                    },
                    "retry_count": 1,
                }
            ]
        },
        headers=tourist_headers,
    )
    assert duplicate_sync_resp.status_code == 200
    dup_data = duplicate_sync_resp.json()
    assert dup_data["duplicate_count"] == 1
    assert dup_data["synced_count"] == 0
    assert dup_data["results"][0]["status"] == "DUPLICATE"
    assert dup_data["results"][0]["server_id"] == str(incident_server_id)

    # 8. Authority Dispatcher Verification:
    # Query incidents as Authority — verify EXACTLY ONE incident exists for this tourist!
    auth_list_resp = client.get(
        "/api/v1/incidents",
        headers=authority_headers,
    )
    assert auth_list_resp.status_code == 200
    incidents_list = auth_list_resp.json()
    tourist_incidents = [
        inc for inc in incidents_list if inc["tourist_id"] == str(tourist.id)
    ]
    assert len(tourist_incidents) == 1
    assert tourist_incidents[0]["id"] == str(incident_server_id)
    assert tourist_incidents[0]["severity"] == "CRITICAL"
