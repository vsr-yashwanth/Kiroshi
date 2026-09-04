import json
import pytest
from datetime import datetime, timezone, timedelta
from starlette.testclient import TestClient

from backend.app.core.security import create_access_token
from backend.app.domain.models.enums import UserRole, GeoZoneType, RiskLevel, RecommendedAction


def test_complete_v03_risk_engine_workflow(client: TestClient):
    """
    KIROSHI v0.3 End-to-End Vertical Slice Workflow:
    1. Register & authenticate Tourist + Authority
    2. Authority creates a HIGH_RISK GeoZone
    3. Tourist creates trip with planned Itinerary waypoints
    4. Tourist starts trip
    5. Authority connects to live WebSocket stream with subscribe_risk=true
    6. Tourist ingests on-route GPS telemetry -> Evaluates to SAFE baseline
    7. Tourist ingests GPS telemetry inside HIGH_RISK GeoZone and off-route -> Risk escalates to HIGH/CRITICAL
    8. RiskAssessment is verified in database with all transparent signals, explanation, and confidence
    9. Authority WebSocket receives real-time RISK_UPDATE with complete explainability payload
    10. Authority inspects current risk and risk history timeline
    11. Security: Unauthorized access rejected
    """
    now = datetime.now(timezone.utc)

    # 1. Register & Authenticate Authority
    auth_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "safety.chief@kiroshi.internal",
            "password": "AuthoritySecurePass123!",
            "full_name": "Chief Safety Inspector",
            "role": UserRole.AUTHORITY.value,
        },
    )
    assert auth_resp.status_code == 201
    auth_id = auth_resp.json()["id"]
    authority_token = create_access_token(subject=auth_id, role=UserRole.AUTHORITY.value)
    authority_headers = {"Authorization": f"Bearer {authority_token}"}

    # Register & Authenticate Tourist
    tourist_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "kenji.sato@example.com",
            "password": "TouristPass12345!",
            "full_name": "Kenji Sato",
            "role": UserRole.TOURIST.value,
        },
    )
    assert tourist_resp.status_code == 201
    tourist_id = tourist_resp.json()["id"]
    tourist_token = create_access_token(subject=tourist_id, role=UserRole.TOURIST.value)
    tourist_headers = {"Authorization": f"Bearer {tourist_token}"}

    # 2. Authority creates a HIGH_RISK GeoZone (Avalanche Gorge)
    zone_resp = client.post(
        "/api/v1/zones",
        headers=authority_headers,
        json={
            "name": "Mount Hiei High-Danger Ravine",
            "description": "Steep unmaintained cliffside with rockfall risk",
            "zone_type": GeoZoneType.HIGH_RISK.value,
            "coordinates": [
                [135.80, 35.05],
                [135.85, 35.05],
                [135.85, 35.10],
                [135.80, 35.10],
                [135.80, 35.05],
            ],
        },
    )
    assert zone_resp.status_code == 201
    zone_id = zone_resp.json()["id"]

    # 3. Tourist creates trip with planned Itinerary waypoints
    trip_resp = client.post(
        "/api/v1/trips",
        headers=tourist_headers,
        json={
            "title": "Hiei Mountain Pilgrimage",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=5)).isoformat(),
            "itineraries": [
                {
                    "destination_name": "Trailhead Checkpoint",
                    "latitude": 35.0200,
                    "longitude": 135.7500,
                    "sequence_order": 1,
                },
                {
                    "destination_name": "Sanctuary Rest Area",
                    "latitude": 35.0350,
                    "longitude": 135.7650,
                    "sequence_order": 2,
                },
            ],
        },
    )
    assert trip_resp.status_code == 201
    trip_id = trip_resp.json()["id"]

    # 4. Tourist starts trip
    start_resp = client.post(f"/api/v1/trips/{trip_id}/start", headers=tourist_headers)
    assert start_resp.status_code == 200

    # 5. Authority connects to WebSocket with risk subscription
    with client.websocket_connect(f"/api/v1/ws/authority?token={authority_token}&subscribe_risk=true") as ws:
        # Receive and discard initial snapshot
        msg_snap = json.loads(ws.receive_text())
        assert msg_snap["type"] == "INITIAL_SNAPSHOT"

        # 6. Tourist ingests nominal on-route telemetry
        t1 = now - timedelta(minutes=10)
        loc1_resp = client.post(
            "/api/v1/location",
            headers=tourist_headers,
            json={
                "trip_id": trip_id,
                "latitude": 35.0205,
                "longitude": 135.7505,
                "accuracy": 4.0,
                "speed": 1.2,
                "recorded_at": t1.isoformat(),
            },
        )
        assert loc1_resp.status_code == 201

        # WebSocket receives LOCATION_UPDATE indicating nominal SAFE state
        msg_loc1 = json.loads(ws.receive_text())
        assert msg_loc1["type"] == "LOCATION_UPDATE"
        assert msg_loc1["data"]["risk_level"] == "SAFE"
        assert msg_loc1["data"]["risk_score"] < 0.20

        # 7. Tourist deviates far into the HIGH_RISK GeoZone (lat=35.07, lng=135.82)
        t2 = now
        loc2_resp = client.post(
            "/api/v1/location",
            headers=tourist_headers,
            json={
                "trip_id": trip_id,
                "latitude": 35.0700,
                "longitude": 135.8200,
                "accuracy": 5.0,
                "speed": 0.5,
                "recorded_at": t2.isoformat(),
            },
        )
        assert loc2_resp.status_code == 201

        # WebSocket receives: LOCATION_UPDATE, ZONE_ENTER, RISK_UPDATE, and v0.4 INCIDENT_CREATED
        received_messages = []
        for _ in range(4):
            received_messages.append(json.loads(ws.receive_text()))
        msg_types = [m["type"] for m in received_messages]
        assert "LOCATION_UPDATE" in msg_types
        assert "ZONE_ENTER" in msg_types
        assert "RISK_UPDATE" in msg_types

        # Inspect the RISK_UPDATE payload
        risk_msg = next(m for m in received_messages if m["type"] == "RISK_UPDATE")
        risk_data = risk_msg["data"]
        assert risk_data["tourist_id"] == tourist_id
        assert risk_data["trip_id"] == trip_id
        assert risk_data["risk_level"] in ["MEDIUM", "HIGH", "CRITICAL"]
        assert risk_data["risk_score"] >= 0.40
        assert risk_data["confidence"] > 0.50
        assert len(risk_data["contributing_signals"]) >= 1
        assert "high-risk" in risk_data["explanation"].lower() or "perimeter" in risk_data["explanation"].lower() or "deviation" in risk_data["explanation"].lower()
        assert risk_data["model_version"] == "v0.3-rule-engine"
        assert risk_data["recommended_action"] in [
            RecommendedAction.REVIEW.value,
            RecommendedAction.CONTACT_TOURIST.value,
            RecommendedAction.ESCALATE_FOR_HUMAN_REVIEW.value,
        ]

    # 8. Verify RiskAssessment persisted in Database via REST API
    curr_risk_resp = client.get(f"/api/v1/risk/current/{tourist_id}", headers=authority_headers)
    assert curr_risk_resp.status_code == 200
    curr_risk = curr_risk_resp.json()
    assert curr_risk["risk_score"] == risk_data["risk_score"]
    assert curr_risk["risk_level"] == risk_data["risk_level"]
    assert curr_risk["model_version"] == "v0.3-rule-engine"

    # 9. Verify Risk History Timeline
    hist_resp = client.get(f"/api/v1/risk/history/{trip_id}", headers=authority_headers)
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) == 2  # 1st nominal + 2nd elevated
    # Ordered descending by created_at
    assert history[0]["risk_score"] > history[1]["risk_score"]

    # 10. Security: Another tourist cannot view Kenji's risk profile or history
    intruder_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "intruder@example.com",
            "password": "IntruderPass12345!",
            "full_name": "Intruder User",
            "role": UserRole.TOURIST.value,
        },
    )
    intruder_token = create_access_token(subject=intruder_resp.json()["id"], role=UserRole.TOURIST.value)
    intruder_headers = {"Authorization": f"Bearer {intruder_token}"}

    forbidden_curr = client.get(f"/api/v1/risk/current/{tourist_id}", headers=intruder_headers)
    assert forbidden_curr.status_code == 403

    forbidden_hist = client.get(f"/api/v1/risk/history/{trip_id}", headers=intruder_headers)
    assert forbidden_hist.status_code == 403
