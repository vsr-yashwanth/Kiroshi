import pytest
from datetime import datetime, timezone, timedelta
from starlette.testclient import TestClient
from backend.app.core.security import create_access_token
from backend.app.domain.models.enums import UserRole, RiskLevel, RecommendedAction


def test_unauthenticated_risk_endpoints_rejected(client: TestClient):
    resp_curr = client.get("/api/v1/risk/current/00000000-0000-0000-0000-000000000000")
    assert resp_curr.status_code == 401

    resp_hist = client.get("/api/v1/risk/history/00000000-0000-0000-0000-000000000000")
    assert resp_hist.status_code == 401

    resp_active = client.get("/api/v1/risk/active")
    assert resp_active.status_code == 401


def test_tourist_cannot_access_other_tourist_risk(
    client: TestClient,
    tourist_user,
    tourist_token_headers: dict,
):
    other_tourist_id = "11111111-1111-1111-1111-111111111111"
    resp = client.get(f"/api/v1/risk/current/{other_tourist_id}", headers=tourist_token_headers)
    assert resp.status_code == 403
    assert "cannot view" in resp.json()["detail"].lower() or "another tourist" in resp.json()["detail"].lower()


def test_tourist_cannot_access_active_fleet_risk(
    client: TestClient,
    tourist_token_headers: dict,
):
    resp = client.get("/api/v1/risk/active", headers=tourist_token_headers)
    assert resp.status_code == 403


def test_authority_can_query_active_risk_and_tourist_risk(
    client: TestClient,
    authority_user,
    tourist_user,
    tourist_token_headers: dict,
):
    authority_token = create_access_token(subject=authority_user.id, role=UserRole.AUTHORITY.value)
    authority_headers = {"Authorization": f"Bearer {authority_token}"}

    # 1. Authority can query active risk fleet snapshot (initially empty or has active tourists)
    active_resp = client.get("/api/v1/risk/active", headers=authority_headers)
    assert active_resp.status_code == 200
    assert isinstance(active_resp.json(), list)

    # 2. Tourist starts trip and sends location
    now = datetime.now(timezone.utc)
    trip_resp = client.post(
        "/api/v1/trips",
        headers=tourist_token_headers,
        json={
            "title": "Kyoto Cultural Journey",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=3)).isoformat(),
        },
    )
    trip_id = trip_resp.json()["id"]
    client.post(f"/api/v1/trips/{trip_id}/start", headers=tourist_token_headers)

    loc_resp = client.post(
        "/api/v1/location",
        headers=tourist_token_headers,
        json={
            "trip_id": trip_id,
            "latitude": 35.0116,
            "longitude": 135.7681,
            "accuracy": 5.0,
            "speed": 1.2,
            "recorded_at": now.isoformat(),
        },
    )
    assert loc_resp.status_code == 201

    # 3. Tourist queries own current risk
    t_curr_resp = client.get(f"/api/v1/risk/current/{tourist_user.id}", headers=tourist_token_headers)
    assert t_curr_resp.status_code == 200
    t_data = t_curr_resp.json()
    assert t_data["tourist_id"] == str(tourist_user.id)
    assert t_data["risk_level"] in [r.value for r in RiskLevel]
    assert "explanation" in t_data
    assert "recommended_action" in t_data
    assert t_data["model_version"] == "v0.3-rule-engine"

    # 4. Authority queries tourist current risk
    auth_curr_resp = client.get(f"/api/v1/risk/current/{tourist_user.id}", headers=authority_headers)
    assert auth_curr_resp.status_code == 200
    assert auth_curr_resp.json()["tourist_id"] == str(tourist_user.id)

    # 5. Tourist queries trip risk history
    hist_resp = client.get(f"/api/v1/risk/history/{trip_id}", headers=tourist_token_headers)
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) >= 1
    assert history[0]["trip_id"] == trip_id
    assert history[0]["confidence"] > 0.0

    # 6. Authority verifies tourist is in active risk snapshot
    active_now = client.get("/api/v1/risk/active", headers=authority_headers).json()
    assert any(item["tourist_id"] == str(tourist_user.id) for item in active_now)
