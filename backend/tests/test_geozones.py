import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from backend.app.domain.models.enums import GeoZoneType, ZoneEventType


def test_create_geozone_success(client: TestClient, authority_token_headers: dict):
    # Square polygon bounding [135.0, 35.0] to [135.1, 35.1]
    coords = [
        [135.0, 35.0],
        [135.1, 35.0],
        [135.1, 35.1],
        [135.0, 35.1],
        [135.0, 35.0],
    ]
    resp = client.post(
        "/api/v1/zones",
        headers=authority_token_headers,
        json={
            "name": "Kyoto Safety Zone A",
            "description": "Monitored tourist precinct",
            "zone_type": GeoZoneType.SAFE.value,
            "coordinates": coords,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Kyoto Safety Zone A"
    assert data["zone_type"] == GeoZoneType.SAFE.value
    assert len(data["coordinates"]) == 5
    assert data["is_active"] is True


def test_tourist_cannot_create_geozone(client: TestClient, tourist_token_headers: dict):
    coords = [
        [135.0, 35.0],
        [135.1, 35.0],
        [135.1, 35.1],
        [135.0, 35.1],
        [135.0, 35.0],
    ]
    resp = client.post(
        "/api/v1/zones",
        headers=tourist_token_headers,
        json={
            "name": "Unauthorized Zone",
            "zone_type": GeoZoneType.SAFE.value,
            "coordinates": coords,
        },
    )
    assert resp.status_code == 403


def test_geozone_duplicate_name_fails(client: TestClient, authority_token_headers: dict):
    coords = [
        [135.0, 35.0],
        [135.1, 35.0],
        [135.1, 35.1],
        [135.0, 35.1],
        [135.0, 35.0],
    ]
    client.post(
        "/api/v1/zones",
        headers=authority_token_headers,
        json={
            "name": "Heritage Precinct",
            "zone_type": GeoZoneType.SAFE.value,
            "coordinates": coords,
        },
    )
    duplicate_resp = client.post(
        "/api/v1/zones",
        headers=authority_token_headers,
        json={
            "name": "Heritage Precinct",
            "zone_type": GeoZoneType.RESTRICTED.value,
            "coordinates": coords,
        },
    )
    assert duplicate_resp.status_code == 409


def test_geozone_enter_and_exit_transitions(
    client: TestClient,
    tourist_token_headers: dict,
    authority_token_headers: dict,
):
    # 1. Authority creates a HIGH_RISK GeoZone
    # Polygon bounding [135.0, 35.0] to [135.2, 35.2]
    coords = [
        [135.0, 35.0],
        [135.2, 35.0],
        [135.2, 35.2],
        [135.0, 35.2],
        [135.0, 35.0],
    ]
    zone_resp = client.post(
        "/api/v1/zones",
        headers=authority_token_headers,
        json={
            "name": "Mt Hiei Cliff Path",
            "description": "Steep rocky trail prone to landslides",
            "zone_type": GeoZoneType.HIGH_RISK.value,
            "coordinates": coords,
        },
    )
    assert zone_resp.status_code == 201
    zone_id = zone_resp.json()["id"]

    # 2. Tourist starts trip
    now = datetime.now(timezone.utc)
    trip_resp = client.post(
        "/api/v1/trips",
        headers=tourist_token_headers,
        json={
            "title": "Mountain Hike",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=2)).isoformat(),
        },
    )
    trip_id = trip_resp.json()["id"]
    client.post(f"/api/v1/trips/{trip_id}/start", headers=tourist_token_headers)

    # 3. Location 1: OUTSIDE the zone (lat=34.9, lng=134.9)
    client.post(
        "/api/v1/location",
        headers=tourist_token_headers,
        json={
            "trip_id": trip_id,
            "latitude": 34.9,
            "longitude": 134.9,
            "accuracy": 10.0,
            "recorded_at": (now - timedelta(minutes=10)).isoformat(),
        },
    )
    # Verify no zone events generated yet
    events_res1 = client.get("/api/v1/zones/events", headers=authority_token_headers)
    assert len(events_res1.json()) == 0

    # 4. Location 2: INSIDE the zone (lat=35.1, lng=135.1) -> triggers outside -> inside (ENTER)
    client.post(
        "/api/v1/location",
        headers=tourist_token_headers,
        json={
            "trip_id": trip_id,
            "latitude": 35.1,
            "longitude": 135.1,
            "accuracy": 8.0,
            "recorded_at": (now - timedelta(minutes=5)).isoformat(),
        },
    )
    events_res2 = client.get("/api/v1/zones/events", headers=authority_token_headers)
    events2 = events_res2.json()
    assert len(events2) == 1
    assert events2[0]["event_type"] == ZoneEventType.ENTER.value
    assert events2[0]["zone_id"] == zone_id

    # 5. Location 3: STILL INSIDE the zone (lat=35.15, lng=135.15) -> inside -> inside (NO duplicate ENTER)
    client.post(
        "/api/v1/location",
        headers=tourist_token_headers,
        json={
            "trip_id": trip_id,
            "latitude": 35.15,
            "longitude": 135.15,
            "accuracy": 8.0,
            "recorded_at": (now - timedelta(minutes=2)).isoformat(),
        },
    )
    events_res3 = client.get("/api/v1/zones/events", headers=authority_token_headers)
    events3 = events_res3.json()
    # Count should STILL be 1! No duplicate ENTER!
    assert len(events3) == 1

    # 6. Location 4: OUTSIDE the zone (lat=34.9, lng=134.9) -> triggers inside -> outside (EXIT)
    client.post(
        "/api/v1/location",
        headers=tourist_token_headers,
        json={
            "trip_id": trip_id,
            "latitude": 34.9,
            "longitude": 134.9,
            "accuracy": 10.0,
            "recorded_at": now.isoformat(),
        },
    )
    events_res4 = client.get("/api/v1/zones/events", headers=authority_token_headers)
    events4 = events_res4.json()
    # Now there should be 2 events: ENTER and EXIT!
    assert len(events4) == 2
    types = [e["event_type"] for e in events4]
    assert ZoneEventType.ENTER.value in types
    assert ZoneEventType.EXIT.value in types

    # 7. Location 5: STILL OUTSIDE (lat=34.8, lng=134.8) -> outside -> outside (NO duplicate EXIT)
    client.post(
        "/api/v1/location",
        headers=tourist_token_headers,
        json={
            "trip_id": trip_id,
            "latitude": 34.8,
            "longitude": 134.8,
            "accuracy": 10.0,
            "recorded_at": (now + timedelta(seconds=10)).isoformat(),
        },
    )
    events_res5 = client.get("/api/v1/zones/events", headers=authority_token_headers)
    events5 = events_res5.json()
    assert len(events5) == 2
