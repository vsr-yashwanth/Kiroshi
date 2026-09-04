import json
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.app.core.security import create_access_token
from backend.app.domain.models.enums import UserRole


def test_websocket_missing_token_rejected(client: TestClient):
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/api/v1/ws/authority"):
            pass
    assert exc_info.value.code == 1008


def test_websocket_invalid_token_rejected(client: TestClient):
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/api/v1/ws/authority?token=invalid.token.here"):
            pass
    assert exc_info.value.code == 1008


def test_websocket_tourist_role_rejected(client: TestClient, tourist_user):
    token = create_access_token(subject=tourist_user.id, role=UserRole.TOURIST.value)
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/api/v1/ws/authority?token={token}"):
            pass
    assert exc_info.value.code == 1008


def test_websocket_authority_connect_and_snapshot(client: TestClient, authority_user):
    token = create_access_token(subject=authority_user.id, role=UserRole.AUTHORITY.value)
    with client.websocket_connect(f"/api/v1/ws/authority?token={token}") as ws:
        # 1. First message received must be INITIAL_SNAPSHOT
        msg = ws.receive_text()
        data = json.loads(msg)
        assert data["type"] == "INITIAL_SNAPSHOT"
        assert isinstance(data["data"], list)

        # 2. Test ping / pong
        ws.send_text(json.dumps({"type": "PING"}))
        pong_msg = ws.receive_text()
        pong_data = json.loads(pong_msg)
        assert pong_data["type"] == "PONG"


def test_websocket_receives_live_location_broadcast(
    client: TestClient,
    authority_user,
    tourist_user,
    tourist_token_headers: dict,
):
    authority_token = create_access_token(subject=authority_user.id, role=UserRole.AUTHORITY.value)

    # 1. Tourist starts trip
    now = datetime.now(timezone.utc)
    create_trip_resp = client.post(
        "/api/v1/trips",
        headers=tourist_token_headers,
        json={
            "title": "Live Monitored Journey",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=2)).isoformat(),
        },
    )
    trip_id = create_trip_resp.json()["id"]
    client.post(f"/api/v1/trips/{trip_id}/start", headers=tourist_token_headers)

    # 2. Authority connects to live WebSocket stream
    with client.websocket_connect(f"/api/v1/ws/authority?token={authority_token}") as ws:
        # Discard initial snapshot
        snapshot_msg = ws.receive_text()
        assert json.loads(snapshot_msg)["type"] == "INITIAL_SNAPSHOT"

        # 3. Tourist ingests location
        ingest_resp = client.post(
            "/api/v1/location",
            headers=tourist_token_headers,
            json={
                "trip_id": trip_id,
                "latitude": 35.6895,
                "longitude": 139.6917,
                "accuracy": 5.0,
                "speed": 2.5,
                "heading": 180.0,
                "recorded_at": now.isoformat(),
            },
        )
        assert ingest_resp.status_code == 201

        # 4. WebSocket must receive the LOCATION_UPDATE broadcast
        live_msg = ws.receive_text()
        live_data = json.loads(live_msg)
        assert live_data["type"] == "LOCATION_UPDATE"
        payload = live_data["data"]
        assert payload["tourist_id"] == str(tourist_user.id)
        assert payload["latitude"] == 35.6895
        assert payload["longitude"] == 139.6917
        assert payload["speed"] == 2.5
        assert payload["trip_title"] == "Live Monitored Journey"
