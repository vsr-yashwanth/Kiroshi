from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.domain.models.enums import (
    UserRole,
    AuditEventType,
    AuditOutcome,
    IncidentStatus,
)
from backend.app.services.audit_service import AuditService


def test_v07_e2e_cross_milestone_audit_chain(
    client: TestClient,
    tourist_token_headers: dict,
    authority_token_headers: dict,
    admin_token_headers: dict,
    responder_token_headers: dict,
    db_session: Session,
):
    """
    End-to-End Test for Milestone v0.7:
    1. Tourist registers and logs in.
    2. Tourist creates and starts a trip.
    3. Tourist triggers emergency SOS.
    4. Authority inspects tourist profile & retrieves active positions snapshot.
    5. Authority transitions incident status and assigns responder.
    6. Responder starts response.
    7. Authority triggers CCTV investigation.
    8. Authority verifies complete cryptographic audit chain.
    9. Admin exports audit trail with un-erasable proof.
    """
    # 1. Profile Read / Update
    p_res = client.get("/api/v1/tourists/me", headers=tourist_token_headers)
    assert p_res.status_code == 200

    u_res = client.put(
        "/api/v1/tourists/me",
        headers=tourist_token_headers,
        json={"medical_notes": "Allergic to penicillin", "consent_given": True},
    )
    assert u_res.status_code == 200

    # 2. Tourist Creates & Starts Trip
    now = datetime.now(timezone.utc)
    trip_res = client.post(
        "/api/v1/trips",
        headers=tourist_token_headers,
        json={
            "title": "Mt. Fuji Alpine Ascent",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=2)).isoformat(),
        },
    )
    assert trip_res.status_code == 201
    trip_id = trip_res.json()["id"]
    client.post(f"/api/v1/trips/{trip_id}/start", headers=tourist_token_headers)

    # Ingest Location
    client.post(
        "/api/v1/location",
        headers=tourist_token_headers,
        json={
            "trip_id": trip_id,
            "latitude": 35.3606,
            "longitude": 138.7274,
            "accuracy": 5.0,
            "recorded_at": now.isoformat(),
        },
    )

    # 3. Emergency SOS
    sos_res = client.post(
        "/api/v1/incidents/sos",
        headers=tourist_token_headers,
        json={
            "trip_id": trip_id,
            "latitude": 35.3606,
            "longitude": 138.7274,
            "accuracy": 5.0,
            "description": "Possible fall on steep gravel ridge",
            "idempotency_key": f"sos-e2e-v07-{uuid.uuid4()}",
        },
    )
    assert sos_res.status_code == 201
    incident_id = sos_res.json()["id"]

    # 4. Authority Active Tourist Snapshot Read
    act_res = client.get("/api/v1/location/active", headers=authority_token_headers)
    assert act_res.status_code == 200

    # 5. Authority Transitions Status & Assigns Responder
    client.post(
        f"/api/v1/incidents/{incident_id}/transition",
        headers=authority_token_headers,
        json={"to_status": IncidentStatus.VERIFIED.value, "reason": "Confirmed distress signal from high ridge"},
    )

    # Get Responder user ID from token
    me_resp = client.get("/api/v1/auth/me", headers=responder_token_headers)
    responder_id = me_resp.json()["id"]

    client.post(
        f"/api/v1/incidents/{incident_id}/assign",
        headers=authority_token_headers,
        json={"responder_id": responder_id, "notes": "Dispatched alpine search team with medical kit"},
    )

    # 6. Responder starts response
    client.post(
        f"/api/v1/incidents/{incident_id}/transition",
        headers=responder_token_headers,
        json={"to_status": IncidentStatus.RESPONDING.value, "reason": "Search team en route to summit"},
    )

    # 7. CCTV Investigation
    cctv_res = client.post(
        "/api/v1/cctv/investigate",
        headers=authority_token_headers,
        json={
            "incident_id": incident_id,
            "search_radius_meters": 300.0,
        },
    )
    assert cctv_res.status_code == 200

    # 8. Authority Verifies Complete Cryptographic Chain
    verify_res = client.post("/api/v1/audit/verify", headers=authority_token_headers)
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["is_valid"] is True
    assert v_data["status"] == "CHAIN_VALID"
    assert v_data["total_events_verified"] >= 5

    # 9. Admin Exports Audit Log
    export_res = client.post(
        "/api/v1/audit/export",
        headers=admin_token_headers,
        json={"format": "json", "reason": "Post-incident rescue operational review"},
    )
    assert export_res.status_code == 200
    e_data = export_res.json()
    assert e_data["integrity_verified"] is True
    assert e_data["total_exported"] >= 6
