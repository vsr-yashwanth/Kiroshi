from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.domain.models.enums import AuditEventType, AuditOutcome, UserRole
from backend.app.services.audit_service import AuditService


def test_audit_list_requires_authority_or_admin(
    client: TestClient,
    tourist_token_headers: dict,
    responder_token_headers: dict,
    authority_token_headers: dict,
    admin_token_headers: dict,
):
    # Tourist forbidden
    r_tourist = client.get("/api/v1/audit/events", headers=tourist_token_headers)
    assert r_tourist.status_code == 403

    # Responder forbidden
    r_responder = client.get("/api/v1/audit/events", headers=responder_token_headers)
    assert r_responder.status_code == 403

    # Authority allowed
    r_auth = client.get("/api/v1/audit/events", headers=authority_token_headers)
    assert r_auth.status_code == 200

    # Admin allowed
    r_admin = client.get("/api/v1/audit/events", headers=admin_token_headers)
    assert r_admin.status_code == 200


def test_audit_verify_chain_endpoint(
    client: TestClient,
    authority_token_headers: dict,
    db_session: Session,
):
    audit_service = AuditService(db_session)
    # Seed audit events
    audit_service.record_event(
        event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
        action="LOGIN",
        resource_type="USER",
        resource_id="seed-user",
        actor_role="ADMIN",
    )
    audit_service.record_event(
        event_type=AuditEventType.INCIDENT_CREATE,
        action="CREATE_SOS",
        resource_type="INCIDENT",
        resource_id="seed-inc",
        actor_role="TOURIST",
    )

    resp = client.post("/api/v1/audit/verify", headers=authority_token_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "CHAIN_VALID"
    assert data["is_valid"] is True
    assert data["total_events_verified"] >= 2


def test_audit_export_requires_admin_and_creates_audit_record(
    client: TestClient,
    authority_token_headers: dict,
    admin_token_headers: dict,
    db_session: Session,
):
    audit_service = AuditService(db_session)
    audit_service.record_event(
        event_type=AuditEventType.PROFILE_UPDATE,
        action="UPDATE_PROFILE",
        resource_type="TOURIST_PROFILE",
        resource_id="prof-123",
    )

    # Authority cannot export (Admin only)
    r_auth = client.post(
        "/api/v1/audit/export",
        headers=authority_token_headers,
        json={"format": "json", "reason": "Monthly security compliance report"},
    )
    assert r_auth.status_code == 403

    # Admin can export
    r_admin = client.post(
        "/api/v1/audit/export",
        headers=admin_token_headers,
        json={"format": "json", "reason": "Monthly security compliance report"},
    )
    assert r_admin.status_code == 200
    data = r_admin.json()
    assert data["format"] == "json"
    assert data["integrity_verified"] is True
    assert data["total_exported"] >= 1

    # Verify that the export created an audit event for DATA_EXPORT
    events, _ = audit_service.list_events(event_type=AuditEventType.DATA_EXPORT)
    assert len(events) >= 1
    assert events[0].action == "EXPORT"
    assert events[0].details["reason"] == "Monthly security compliance report"
