import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.domain.models.enums import IncidentStatus, IncidentSeverity, IncidentSource


def create_test_sos(client: TestClient, headers: dict) -> dict:
    resp = client.post(
        "/api/v1/incidents/sos",
        headers=headers,
        json={
            "latitude": 35.0116,
            "longitude": 135.7681,
            "accuracy": 5.0,
            "notes": "Emergency test",
            "idempotency_key": f"test-{uuid.uuid4()}",
        },
    )
    assert resp.status_code == 201
    return resp.json()


def test_list_and_get_incidents(
    client: TestClient,
    tourist_token_headers,
    authority_token_headers,
    responder_token_headers,
):
    # Tourist creates an incident
    incident = create_test_sos(client, tourist_token_headers)
    incident_id = incident["id"]

    # Authority can list active incidents
    resp_auth = client.get("/api/v1/incidents", headers=authority_token_headers)
    assert resp_auth.status_code == 200
    incidents_auth = resp_auth.json()
    assert any(i["id"] == incident_id for i in incidents_auth)

    # Authority can get incident by ID
    resp_get = client.get(f"/api/v1/incidents/{incident_id}", headers=authority_token_headers)
    assert resp_get.status_code == 200
    assert resp_get.json()["id"] == incident_id

    # Responder initially has no assigned incidents
    resp_resp = client.get("/api/v1/incidents", headers=responder_token_headers)
    assert resp_resp.status_code == 200
    assert not any(i["id"] == incident_id for i in resp_resp.json())


def test_incident_timeline(client: TestClient, tourist_token_headers, authority_token_headers):
    incident = create_test_sos(client, tourist_token_headers)
    incident_id = incident["id"]

    # Retrieve timeline
    resp = client.get(f"/api/v1/incidents/{incident_id}/timeline", headers=authority_token_headers)
    assert resp.status_code == 200
    timeline = resp.json()
    assert len(timeline) >= 1
    assert timeline[0]["event_type"] == "INCIDENT_CREATED"
    assert timeline[0]["to_status"] == IncidentStatus.DETECTED.value


def test_incident_transition_api(client: TestClient, tourist_token_headers, authority_token_headers):
    incident = create_test_sos(client, tourist_token_headers)
    incident_id = incident["id"]

    # 1. Authority moves DETECTED -> VERIFYING
    resp = client.post(
        f"/api/v1/incidents/{incident_id}/transition",
        headers=authority_token_headers,
        json={"to_status": IncidentStatus.VERIFYING.value, "notes": "Dispatcher contacting tourist"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == IncidentStatus.VERIFYING.value

    # 2. Tourist attempts unauthorized transition -> 403 Forbidden
    unauth_resp = client.post(
        f"/api/v1/incidents/{incident_id}/transition",
        headers=tourist_token_headers,
        json={"to_status": IncidentStatus.VERIFIED.value},
    )
    assert unauth_resp.status_code == 403

    # 3. Authority attempts invalid transition -> 400 Bad Request
    invalid_resp = client.post(
        f"/api/v1/incidents/{incident_id}/transition",
        headers=authority_token_headers,
        json={"to_status": IncidentStatus.RESPONDING.value},
    )
    assert invalid_resp.status_code == 400


def test_responder_assignment_and_reassignment(
    client: TestClient,
    tourist_token_headers,
    authority_token_headers,
    responder_user,
    admin_user,
    db_session,
):
    from backend.app.domain.models.user import User
    from backend.app.domain.models.enums import UserRole
    from backend.app.core.security import get_password_hash

    # Create a second responder
    responder_2 = User(
        email="responder2@example.com",
        hashed_password=get_password_hash("Pass123!"),
        full_name="Officer Sato",
        role=UserRole.RESPONDER,
        is_active=True,
    )
    db_session.add(responder_2)
    db_session.commit()
    db_session.refresh(responder_2)

    incident = create_test_sos(client, tourist_token_headers)
    incident_id = incident["id"]

    # Authority verifies incident first
    client.post(
        f"/api/v1/incidents/{incident_id}/transition",
        headers=authority_token_headers,
        json={"to_status": IncidentStatus.VERIFYING.value},
    )
    client.post(
        f"/api/v1/incidents/{incident_id}/transition",
        headers=authority_token_headers,
        json={"to_status": IncidentStatus.VERIFIED.value},
    )

    # List available responders
    resp_avail = client.get("/api/v1/incidents/responders/available", headers=authority_token_headers)
    assert resp_avail.status_code == 200
    responders = resp_avail.json()
    assert len(responders) >= 2

    # Assign responder 1
    assign_resp = client.post(
        f"/api/v1/incidents/{incident_id}/assign",
        headers=authority_token_headers,
        json={"responder_id": str(responder_user.id), "notes": "Primary dispatch"},
    )
    assert assign_resp.status_code == 200
    assigned_data = assign_resp.json()
    assert assigned_data["status"] == IncidentStatus.ASSIGNED.value
    assert assigned_data["assigned_responder_id"] == str(responder_user.id)

    # Reassign to responder 2 (preserves history)
    reassign_resp = client.post(
        f"/api/v1/incidents/{incident_id}/assign",
        headers=authority_token_headers,
        json={"responder_id": str(responder_2.id), "notes": "Reassigned due to closer proximity"},
    )
    assert reassign_resp.status_code == 200
    reassigned_data = reassign_resp.json()
    assert reassigned_data["assigned_responder_id"] == str(responder_2.id)

    # Check timeline has both assignment events
    timeline_resp = client.get(f"/api/v1/incidents/{incident_id}/timeline", headers=authority_token_headers)
    events = [e["event_type"] for e in timeline_resp.json()]
    assert events.count("INCIDENT_ASSIGNED") == 2
