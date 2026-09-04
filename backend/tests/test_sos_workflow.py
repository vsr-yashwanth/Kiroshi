import uuid
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from backend.app.domain.models.enums import IncidentSeverity, IncidentSource, IncidentStatus, LocationFreshness


def test_sos_with_fresh_location(client: TestClient, tourist_token_headers):
    idempotency_key = f"sos-{uuid.uuid4()}"
    payload = {
        "latitude": 35.0116,
        "longitude": 135.7681,
        "accuracy": 4.5,
        "notes": "Medical emergency on mountain path",
        "idempotency_key": idempotency_key,
    }
    resp = client.post("/api/v1/incidents/sos", headers=tourist_token_headers, json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["source"] == IncidentSource.SOS.value
    assert data["severity"] == IncidentSeverity.CRITICAL.value
    assert data["status"] == IncidentStatus.DETECTED.value
    assert data["latitude"] == 35.0116
    assert data["longitude"] == 135.7681
    assert data["location_freshness"] == LocationFreshness.LIVE.value
    assert data["idempotency_key"] == idempotency_key


def test_sos_with_unavailable_location(client: TestClient, tourist_token_headers):
    """
    When GPS is temporarily unavailable, SOS MUST still create an incident
    with UNKNOWN location freshness.
    """
    idempotency_key = f"sos-{uuid.uuid4()}"
    payload = {
        "latitude": None,
        "longitude": None,
        "notes": "Lost in forest, GPS not fixing",
        "idempotency_key": idempotency_key,
    }
    resp = client.post("/api/v1/incidents/sos", headers=tourist_token_headers, json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["source"] == IncidentSource.SOS.value
    assert data["status"] == IncidentStatus.DETECTED.value
    assert data["latitude"] is None
    assert data["longitude"] is None
    assert data["location_freshness"] == LocationFreshness.UNKNOWN.value


def test_sos_idempotency_duplicate_prevention(client: TestClient, tourist_token_headers):
    """
    Double taps or network retries with the same idempotency_key must return
    the existing incident rather than spawning duplicate incidents.
    """
    idempotency_key = f"sos-duplicate-test-{uuid.uuid4()}"
    payload = {
        "latitude": 35.0200,
        "longitude": 135.7500,
        "notes": "Flash flood warning",
        "idempotency_key": idempotency_key,
    }
    # First submission
    resp1 = client.post("/api/v1/incidents/sos", headers=tourist_token_headers, json=payload)
    assert resp1.status_code == 201
    incident1 = resp1.json()

    # Second submission with identical idempotency_key
    resp2 = client.post("/api/v1/incidents/sos", headers=tourist_token_headers, json=payload)
    assert resp2.status_code in [200, 201]
    incident2 = resp2.json()

    # Must be identical incident ID
    assert incident1["id"] == incident2["id"]


def test_sos_failure_mode_risk_engine_and_ai_unavailable(client: TestClient, tourist_token_headers):
    """
    MANDATORY ACCEPTANCE TEST (Phase 38):
    Even if RiskEngine, ML services, CCTV, or AI throw errors or are unavailable,
    SOS MUST STILL SUCCEED and create an incident.
    """
    with patch("backend.app.engines.risk.evaluator.RiskEvaluator.evaluate", side_effect=RuntimeError("AI Risk Engine Down")):
        idempotency_key = f"sos-offline-ai-{uuid.uuid4()}"
        payload = {
            "latitude": 35.0300,
            "longitude": 135.7700,
            "notes": "Urgent evacuation requested",
            "idempotency_key": idempotency_key,
        }
        resp = client.post("/api/v1/incidents/sos", headers=tourist_token_headers, json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["source"] == IncidentSource.SOS.value
        assert data["status"] == IncidentStatus.DETECTED.value


def test_sos_requires_authentication(client: TestClient):
    payload = {
        "latitude": 35.0116,
        "longitude": 135.7681,
    }
    resp = client.post("/api/v1/incidents/sos", json=payload)
    assert resp.status_code == 401
