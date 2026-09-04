import json
import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from backend.app.core.security import create_access_token
from backend.app.domain.models.enums import (
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
    LocationFreshness,
    UserRole,
)


def test_complete_v04_emergency_response_lifecycle(
    client: TestClient,
    tourist_user,
    tourist_token_headers,
    authority_user,
    authority_token_headers,
    responder_user,
    responder_token_headers,
):
    """
    PHASE 37: End-to-End Emergency Response Lifecycle
    Tourist SOS -> Authority Triage -> Verification -> Escalation -> Assignment ->
    Responder Response -> Resolution -> Authority Closure.
    """
    authority_token = create_access_token(subject=authority_user.id, role=authority_user.role.value)

    # 1. Tourist starts an active trip
    start_date = datetime.now(timezone.utc).isoformat()
    end_date = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    trip_resp = client.post(
        "/api/v1/trips",
        headers=tourist_token_headers,
        json={
            "title": "Mt. Fuji Northern Ascent",
            "start_date": start_date,
            "end_date": end_date,
            "itineraries": [
                {
                    "destination_name": "5th Station",
                    "latitude": 35.3606,
                    "longitude": 138.7274,
                    "sequence_order": 1,
                }
            ],
        },
    )
    assert trip_resp.status_code == 201
    trip_id = trip_resp.json()["id"]

    start_res = client.post(f"/api/v1/trips/{trip_id}/start", headers=tourist_token_headers)
    assert start_res.status_code == 200

    # 2. Authority connects to real-time WebSocket
    with client.websocket_connect(f"/api/v1/ws/authority?token={authority_token}") as ws:
        init_msg = json.loads(ws.receive_text())
        assert init_msg["type"] == "INITIAL_SNAPSHOT"

        # 3. Tourist activates SOS
        idempotency_key = f"sos-e2e-{uuid.uuid4()}"
        sos_resp = client.post(
            "/api/v1/incidents/sos",
            headers=tourist_token_headers,
            json={
                "trip_id": trip_id,
                "latitude": 35.3620,
                "longitude": 138.7300,
                "accuracy": 3.2,
                "notes": "Severe altitude sickness, cannot descend",
                "idempotency_key": idempotency_key,
            },
        )
        assert sos_resp.status_code == 201
        incident = sos_resp.json()
        incident_id = incident["id"]
        assert incident["status"] == IncidentStatus.DETECTED.value
        assert incident["severity"] == IncidentSeverity.CRITICAL.value
        assert incident["source"] == IncidentSource.SOS.value

        # 4. Authority receives real-time INCIDENT_CREATED
        msg_created = json.loads(ws.receive_text())
        assert msg_created["type"] == "INCIDENT_CREATED"
        assert msg_created["data"]["incident_id"] == incident_id

        # 5. Authority transitions: DETECTED -> VERIFYING
        t1_resp = client.post(
            f"/api/v1/incidents/{incident_id}/transition",
            headers=authority_token_headers,
            json={"to_status": IncidentStatus.VERIFYING.value, "notes": "Checking satellite beacon and calling tourist"},
        )
        assert t1_resp.status_code == 200
        assert t1_resp.json()["status"] == IncidentStatus.VERIFYING.value

        msg_t1 = json.loads(ws.receive_text())
        assert msg_t1["type"] == "INCIDENT_STATUS_CHANGED"
        assert msg_t1["data"]["to_status"] == IncidentStatus.VERIFYING.value

        # 6. Authority transitions: VERIFYING -> VERIFIED
        t2_resp = client.post(
            f"/api/v1/incidents/{incident_id}/transition",
            headers=authority_token_headers,
            json={"to_status": IncidentStatus.VERIFIED.value, "notes": "Confirmed SOS via phone contact with companion"},
        )
        assert t2_resp.status_code == 200
        assert t2_resp.json()["status"] == IncidentStatus.VERIFIED.value

        msg_t2 = json.loads(ws.receive_text())
        assert msg_t2["type"] == "INCIDENT_STATUS_CHANGED"
        assert msg_t2["data"]["to_status"] == IncidentStatus.VERIFIED.value

        # 7. Authority transitions: VERIFIED -> ESCALATED
        t3_resp = client.post(
            f"/api/v1/incidents/{incident_id}/transition",
            headers=authority_token_headers,
            json={"to_status": IncidentStatus.ESCALATED.value, "notes": "Escalating to Mountain Mountain Rescue Unit"},
        )
        assert t3_resp.status_code == 200
        assert t3_resp.json()["status"] == IncidentStatus.ESCALATED.value

        msg_t3 = json.loads(ws.receive_text())
        assert msg_t3["type"] == "INCIDENT_STATUS_CHANGED"
        assert msg_t3["data"]["to_status"] == IncidentStatus.ESCALATED.value

        # 8. Authority assigns responder: ESCALATED -> ASSIGNED
        assign_resp = client.post(
            f"/api/v1/incidents/{incident_id}/assign",
            headers=authority_token_headers,
            json={"responder_id": str(responder_user.id), "notes": "Deploying closest mountain unit"},
        )
        assert assign_resp.status_code == 200
        assert assign_resp.json()["status"] == IncidentStatus.ASSIGNED.value
        assert assign_resp.json()["assigned_responder_id"] == str(responder_user.id)

        msg_assign = json.loads(ws.receive_text())
        assert msg_assign["type"] == "INCIDENT_ASSIGNED"
        assert msg_assign["data"]["responder_id"] == str(responder_user.id)

        # 9. Responder sees assigned incident
        resp_list = client.get("/api/v1/incidents", headers=responder_token_headers)
        assert resp_list.status_code == 200
        assigned_incidents = resp_list.json()
        assert any(i["id"] == incident_id for i in assigned_incidents)

        # 10. Responder begins response: ASSIGNED -> RESPONDING
        t4_resp = client.post(
            f"/api/v1/incidents/{incident_id}/transition",
            headers=responder_token_headers,
            json={"to_status": IncidentStatus.RESPONDING.value, "notes": "En route via ATV to 5th station"},
        )
        assert t4_resp.status_code == 200
        assert t4_resp.json()["status"] == IncidentStatus.RESPONDING.value

        msg_t4 = json.loads(ws.receive_text())
        assert msg_t4["type"] == "INCIDENT_STATUS_CHANGED"
        assert msg_t4["data"]["to_status"] == IncidentStatus.RESPONDING.value

        # 11. Responder resolves incident: RESPONDING -> RESOLVED
        t5_resp = client.post(
            f"/api/v1/incidents/{incident_id}/transition",
            headers=responder_token_headers,
            json={"to_status": IncidentStatus.RESOLVED.value, "notes": "Tourist reached, oxygen administered, evacuated safely"},
        )
        assert t5_resp.status_code == 200
        assert t5_resp.json()["status"] == IncidentStatus.RESOLVED.value

        msg_t5 = json.loads(ws.receive_text())
        assert msg_t5["type"] == "INCIDENT_STATUS_CHANGED"
        assert msg_t5["data"]["to_status"] == IncidentStatus.RESOLVED.value

        # 12. Authority closes incident: RESOLVED -> CLOSED
        t6_resp = client.post(
            f"/api/v1/incidents/{incident_id}/transition",
            headers=authority_token_headers,
            json={"to_status": IncidentStatus.CLOSED.value, "notes": "Medical handoff complete, debrief signed off"},
        )
        assert t6_resp.status_code == 200
        assert t6_resp.json()["status"] == IncidentStatus.CLOSED.value

        msg_t6 = json.loads(ws.receive_text())
        assert msg_t6["type"] == "INCIDENT_STATUS_CHANGED"
        assert msg_t6["data"]["to_status"] == IncidentStatus.CLOSED.value

    # 13. Verify full chronological timeline
    timeline_resp = client.get(f"/api/v1/incidents/{incident_id}/timeline", headers=authority_token_headers)
    assert timeline_resp.status_code == 200
    timeline = timeline_resp.json()
    assert len(timeline) >= 7

    event_types = [e["event_type"] for e in timeline]
    assert event_types[0] == "INCIDENT_CREATED"
    assert "INCIDENT_ASSIGNED" in event_types
    assert "RESPONSE_STARTED" in event_types
    assert "INCIDENT_RESOLVED" in event_types
    assert "INCIDENT_CLOSED" in event_types

    # 14. Terminal state rejection: cannot transition a CLOSED incident
    terminal_resp = client.post(
        f"/api/v1/incidents/{incident_id}/transition",
        headers=authority_token_headers,
        json={"to_status": IncidentStatus.RESPONDING.value},
    )
    assert terminal_resp.status_code == 400
