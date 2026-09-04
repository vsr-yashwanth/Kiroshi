import json
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from backend.app.core.security import create_access_token
from backend.app.domain.models.enums import UserRole, GeoZoneType, ZoneEventType, LocationFreshness


def test_complete_v02_geospatial_monitoring_workflow(client: TestClient, db_session):
    # -------------------------------------------------------------
    # 1. Authority setup and authentication
    # -------------------------------------------------------------
    auth_reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "captain.commander@kiroshi.org",
            "password": "AuthoritySecurePass123!",
            "full_name": "Commander Sarah Connor",
            "phone_number": "+1234567890",
            "role": UserRole.AUTHORITY.value,
        },
    )
    assert auth_reg_resp.status_code == 201
    auth_user_id = auth_reg_resp.json()["id"]

    auth_login = client.post(
        "/api/v1/auth/login",
        data={"username": "captain.commander@kiroshi.org", "password": "AuthoritySecurePass123!"},
    )
    assert auth_login.status_code == 200
    authority_token = auth_login.json()["access_token"]
    authority_headers = {"Authorization": f"Bearer {authority_token}"}

    # -------------------------------------------------------------
    # 2. Tourist setup, profile, and active trip
    # -------------------------------------------------------------
    tourist_reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "marco.polo@traveler.com",
            "password": "WanderlustPass123!",
            "full_name": "Marco Polo",
            "phone_number": "+9876543210",
            "role": UserRole.TOURIST.value,
        },
    )
    assert tourist_reg_resp.status_code == 201
    tourist_user_id = tourist_reg_resp.json()["id"]

    tourist_login = client.post(
        "/api/v1/auth/login",
        data={"username": "marco.polo@traveler.com", "password": "WanderlustPass123!"},
    )
    assert tourist_login.status_code == 200
    tourist_token = tourist_login.json()["access_token"]
    tourist_headers = {"Authorization": f"Bearer {tourist_token}"}

    # Update profile consent
    client.put(
        "/api/v1/tourists/me",
        headers=tourist_headers,
        json={
            "nationality": "Italian",
            "emergency_contact_name": "Niccolo Polo",
            "emergency_contact_phone": "+39041123456",
            "consent_given": True,
        },
    )

    # Tourist creates and starts trip
    now = datetime.now(timezone.utc)
    trip_create = client.post(
        "/api/v1/trips",
        headers=tourist_headers,
        json={
            "title": "Venetian Silk Route Expedition",
            "description": "Exploration of mountainous trading passes",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=10)).isoformat(),
        },
    )
    assert trip_create.status_code == 201
    trip_id = trip_create.json()["id"]

    start_trip = client.post(f"/api/v1/trips/{trip_id}/start", headers=tourist_headers)
    assert start_trip.status_code == 200

    # -------------------------------------------------------------
    # 3. Authority creates a RESTRICTED GeoZone
    # Polygon bounding [12.0, 45.0] to [12.5, 45.5]
    # -------------------------------------------------------------
    zone_coords = [
        [12.0, 45.0],
        [12.5, 45.0],
        [12.5, 45.5],
        [12.0, 45.5],
        [12.0, 45.0],
    ]
    zone_resp = client.post(
        "/api/v1/zones",
        headers=authority_headers,
        json={
            "name": "Alpine Avalanche Sector 4",
            "description": "High danger restricted mountain zone",
            "zone_type": GeoZoneType.RESTRICTED.value,
            "coordinates": zone_coords,
        },
    )
    assert zone_resp.status_code == 201
    zone_id = zone_resp.json()["id"]

    # -------------------------------------------------------------
    # 4. Authority opens live WebSocket stream
    # -------------------------------------------------------------
    with client.websocket_connect(f"/api/v1/ws/authority?token={authority_token}") as ws:
        # Initial snapshot
        msg1 = ws.receive_text()
        assert json.loads(msg1)["type"] == "INITIAL_SNAPSHOT"

        # -------------------------------------------------------------
        # 5. Tourist sends GPS point OUTSIDE the zone (lat=44.0, lng=11.0)
        # -------------------------------------------------------------
        t1 = now - timedelta(minutes=15)
        resp_loc1 = client.post(
            "/api/v1/location",
            headers=tourist_headers,
            json={
                "trip_id": trip_id,
                "latitude": 44.0,
                "longitude": 11.0,
                "accuracy": 12.0,
                "speed": 1.5,
                "recorded_at": t1.isoformat(),
            },
        )
        assert resp_loc1.status_code == 201

        # WebSocket receives LOCATION_UPDATE
        ws_loc1 = json.loads(ws.receive_text())
        assert ws_loc1["type"] == "LOCATION_UPDATE"
        assert ws_loc1["data"]["latitude"] == 44.0
        assert ws_loc1["data"]["active_zones"] == []

        # -------------------------------------------------------------
        # 6. Tourist sends GPS point INSIDE the zone (lat=45.2, lng=12.2)
        # -> triggers outside -> inside: exactly 1 ENTER event
        # -------------------------------------------------------------
        t2 = now - timedelta(minutes=10)
        resp_loc2 = client.post(
            "/api/v1/location",
            headers=tourist_headers,
            json={
                "trip_id": trip_id,
                "latitude": 45.2,
                "longitude": 12.2,
                "accuracy": 6.0,
                "speed": 2.0,
                "recorded_at": t2.isoformat(),
            },
        )
        assert resp_loc2.status_code == 201

        # WebSocket receives LOCATION_UPDATE and ZONE_ENTER
        msg_a = json.loads(ws.receive_text())
        msg_b = json.loads(ws.receive_text())
        messages = [msg_a, msg_b]
        types = [m["type"] for m in messages]
        assert "LOCATION_UPDATE" in types
        assert "ZONE_ENTER" in types

        # -------------------------------------------------------------
        # 7. Tourist sends another GPS point STILL INSIDE the zone (lat=45.3, lng=12.3)
        # -> inside -> inside: NO duplicate ENTER event
        # -------------------------------------------------------------
        t3 = now - timedelta(minutes=5)
        resp_loc3 = client.post(
            "/api/v1/location",
            headers=tourist_headers,
            json={
                "trip_id": trip_id,
                "latitude": 45.3,
                "longitude": 12.3,
                "accuracy": 5.0,
                "speed": 1.8,
                "recorded_at": t3.isoformat(),
            },
        )
        assert resp_loc3.status_code == 201

        # WebSocket receives ONLY LOCATION_UPDATE (no zone enter event!)
        ws_loc3 = json.loads(ws.receive_text())
        assert ws_loc3["type"] == "LOCATION_UPDATE"
        assert "Alpine Avalanche Sector 4" in ws_loc3["data"]["active_zones"]

        # -------------------------------------------------------------
        # 8. Tourist sends GPS point OUTSIDE the zone (lat=44.5, lng=11.5)
        # -> inside -> outside: exactly 1 EXIT event
        # -------------------------------------------------------------
        t4 = now
        resp_loc4 = client.post(
            "/api/v1/location",
            headers=tourist_headers,
            json={
                "trip_id": trip_id,
                "latitude": 44.5,
                "longitude": 11.5,
                "accuracy": 7.0,
                "speed": 2.2,
                "recorded_at": t4.isoformat(),
            },
        )
        assert resp_loc4.status_code == 201

        msg_c = json.loads(ws.receive_text())
        msg_d = json.loads(ws.receive_text())
        messages_exit = [msg_c, msg_d]
        types_exit = [m["type"] for m in messages_exit]
        assert "LOCATION_UPDATE" in types_exit
        assert "ZONE_EXIT" in types_exit

    # -------------------------------------------------------------
    # 9. Authority verifies audit log and active tourists view
    # -------------------------------------------------------------
    events_resp = client.get("/api/v1/zones/events", headers=authority_headers)
    assert events_resp.status_code == 200
    recorded_events = events_resp.json()
    assert len(recorded_events) == 2
    event_types = [e["event_type"] for e in recorded_events]
    assert ZoneEventType.ENTER.value in event_types
    assert ZoneEventType.EXIT.value in event_types

    active_resp = client.get("/api/v1/location/active", headers=authority_headers)
    assert active_resp.status_code == 200
    active_tourists = active_resp.json()
    assert len(active_tourists) == 1
    t_pos = active_tourists[0]
    assert t_pos["tourist_name"] == "Marco Polo"
    assert t_pos["latitude"] == 44.5
    assert t_pos["longitude"] == 11.5
    assert t_pos["freshness"] == LocationFreshness.LIVE.value

    # Verify trip breadcrumb history
    history_resp = client.get(f"/api/v1/location/history/{trip_id}", headers=authority_headers)
    assert history_resp.status_code == 200
    breadcrumbs = history_resp.json()
    assert len(breadcrumbs) == 4
