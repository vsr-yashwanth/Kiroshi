import uuid
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from backend.app.domain.models.enums import IncidentStatus, NotificationDeliveryStatus


def test_notification_created_and_marked_as_read(
    client: TestClient,
    tourist_token_headers,
    authority_token_headers,
):
    # 1. Tourist triggers SOS
    resp = client.post(
        "/api/v1/incidents/sos",
        headers=tourist_token_headers,
        json={
            "latitude": 35.0116,
            "longitude": 135.7681,
            "accuracy": 5.0,
            "notes": "SOS for notification test",
            "idempotency_key": f"notif-test-{uuid.uuid4()}",
        },
    )
    assert resp.status_code == 201
    incident = resp.json()

    # 2. Authority fetches notifications
    notif_resp = client.get("/api/v1/notifications", headers=authority_token_headers)
    assert notif_resp.status_code == 200
    notifications = notif_resp.json()
    assert len(notifications) >= 1

    # Find the emergency SOS notification
    sos_notif = next(
        (n for n in notifications if n.get("incident_id") == incident["id"]),
        None,
    )
    assert sos_notif is not None
    assert sos_notif["status"] == NotificationDeliveryStatus.SENT.value
    assert sos_notif["is_read"] is False

    # 3. Mark notification as read
    read_resp = client.put(
        f"/api/v1/notifications/{sos_notif['id']}/read",
        headers=authority_token_headers,
    )
    assert read_resp.status_code == 200
    updated_notif = read_resp.json()
    assert updated_notif["is_read"] is True


def test_incident_persistence_guaranteed_on_notification_failure(
    client: TestClient,
    tourist_token_headers,
    authority_token_headers,
):
    """
    CRITICAL RELIABILITY REQUIREMENT (Phase 22):
    If notification dispatch fails or raises an error, incident creation
    MUST STILL SUCCEED and be persisted. Notification failure must NEVER roll back
    the emergency incident.
    """
    with patch(
        "backend.app.services.notification_service.InAppNotificationProvider.deliver",
        side_effect=RuntimeError("Notification Network Disruption"),
    ):
        idempotency_key = f"fault-notif-{uuid.uuid4()}"
        resp = client.post(
            "/api/v1/incidents/sos",
            headers=tourist_token_headers,
            json={
                "latitude": 35.0500,
                "longitude": 135.7800,
                "notes": "Emergency during notification outage",
                "idempotency_key": idempotency_key,
            },
        )
        # Incident creation MUST succeed
        assert resp.status_code == 201
        incident_id = resp.json()["id"]

        # Incident is retrievable by Authority
        get_resp = client.get(f"/api/v1/incidents/{incident_id}", headers=authority_token_headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == incident_id
