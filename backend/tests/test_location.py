import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from backend.app.domain.models.enums import TripStatus, LocationFreshness


def test_ingest_location_success(client: TestClient, tourist_token_headers: dict):
    # 1. Create and start an active trip
    now = datetime.now(timezone.utc)
    create_trip_resp = client.post(
        "/api/v1/trips",
        headers=tourist_token_headers,
        json={
            "title": "Kyoto Cultural Tour",
            "description": "Visiting historical shrines and temples",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=5)).isoformat(),
            "itineraries": [
                {
                    "destination_name": "Fushimi Inari",
                    "latitude": 34.9671,
                    "longitude": 135.7727,
                    "sequence_order": 1,
                }
            ],
        },
    )
    assert create_trip_resp.status_code == 201
    trip_id = create_trip_resp.json()["id"]

    # Start trip
    start_resp = client.post(f"/api/v1/trips/{trip_id}/start", headers=tourist_token_headers)
    assert start_resp.status_code == 200

    # 2. Ingest valid GPS location
    loc_resp = client.post(
        "/api/v1/location",
        headers=tourist_token_headers,
        json={
            "trip_id": trip_id,
            "latitude": 34.9675,
            "longitude": 135.7730,
            "accuracy": 8.5,
            "altitude": 55.0,
            "speed": 1.2,
            "heading": 90.0,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert loc_resp.status_code == 201
    data = loc_resp.json()
    assert data["latitude"] == 34.9675
    assert data["longitude"] == 135.7730
    assert data["accuracy"] == 8.5
    assert data["speed"] == 1.2
    assert data["freshness"] == LocationFreshness.LIVE.value
    assert data["trip_id"] == trip_id


def test_ingest_location_invalid_coordinates(client: TestClient, tourist_token_headers: dict):
    # Latitude > 90
    resp1 = client.post(
        "/api/v1/location",
        headers=tourist_token_headers,
        json={
            "trip_id": str(uuid.uuid4()),
            "latitude": 95.0,
            "longitude": 100.0,
            "accuracy": 10.0,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert resp1.status_code == 422

    # Longitude > 180
    resp2 = client.post(
        "/api/v1/location",
        headers=tourist_token_headers,
        json={
            "trip_id": str(uuid.uuid4()),
            "latitude": 45.0,
            "longitude": 185.0,
            "accuracy": 10.0,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert resp2.status_code == 422


def test_ingest_location_invalid_accuracy(client: TestClient, tourist_token_headers: dict):
    # Accuracy <= 0
    resp = client.post(
        "/api/v1/location",
        headers=tourist_token_headers,
        json={
            "trip_id": str(uuid.uuid4()),
            "latitude": 34.9675,
            "longitude": 135.7730,
            "accuracy": 0.0,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert resp.status_code == 422


def test_ingest_location_future_clock_skew_fails(client: TestClient, tourist_token_headers: dict):
    # 1. Create and start trip
    now = datetime.now(timezone.utc)
    create_trip_resp = client.post(
        "/api/v1/trips",
        headers=tourist_token_headers,
        json={
            "title": "Tokyo Explorations",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=3)).isoformat(),
        },
    )
    trip_id = create_trip_resp.json()["id"]
    client.post(f"/api/v1/trips/{trip_id}/start", headers=tourist_token_headers)

    # 2. Submit timestamp 10 minutes in the future (> 300s skew)
    future_time = now + timedelta(minutes=10)
    resp = client.post(
        "/api/v1/location",
        headers=tourist_token_headers,
        json={
            "trip_id": trip_id,
            "latitude": 35.6762,
            "longitude": 139.6503,
            "accuracy": 10.0,
            "recorded_at": future_time.isoformat(),
        },
    )
    assert resp.status_code == 400
    assert "future" in resp.json()["detail"].lower()


def test_ingest_location_inactive_trip_fails(client: TestClient, tourist_token_headers: dict):
    # Create trip in PLANNED status (do NOT start it)
    now = datetime.now(timezone.utc)
    create_trip_resp = client.post(
        "/api/v1/trips",
        headers=tourist_token_headers,
        json={
            "title": "Future Hokkaido Trip",
            "start_date": (now + timedelta(days=10)).isoformat(),
            "end_date": (now + timedelta(days=15)).isoformat(),
        },
    )
    trip_id = create_trip_resp.json()["id"]

    resp = client.post(
        "/api/v1/location",
        headers=tourist_token_headers,
        json={
            "trip_id": trip_id,
            "latitude": 43.0618,
            "longitude": 141.3545,
            "accuracy": 10.0,
            "recorded_at": now.isoformat(),
        },
    )
    assert resp.status_code == 400
    assert "active" in resp.json()["detail"].lower()


def test_cross_tourist_location_submission_forbidden(
    client: TestClient,
    tourist_token_headers: dict,
    tourist_2_token_headers: dict,
):
    # Tourist 1 creates and starts a trip
    now = datetime.now(timezone.utc)
    create_trip_resp = client.post(
        "/api/v1/trips",
        headers=tourist_token_headers,
        json={
            "title": "Tourist 1 Solo Trek",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=2)).isoformat(),
        },
    )
    trip_id = create_trip_resp.json()["id"]
    client.post(f"/api/v1/trips/{trip_id}/start", headers=tourist_token_headers)

    # Tourist 2 attempts to submit location for Tourist 1's trip (IDOR attempt)
    resp = client.post(
        "/api/v1/location",
        headers=tourist_2_token_headers,
        json={
            "trip_id": trip_id,
            "latitude": 35.6762,
            "longitude": 139.6503,
            "accuracy": 10.0,
            "recorded_at": now.isoformat(),
        },
    )
    assert resp.status_code == 403
    assert "another tourist's trip" in resp.json()["detail"].lower()


def test_trip_location_history_access_control(
    client: TestClient,
    tourist_token_headers: dict,
    tourist_2_token_headers: dict,
    authority_token_headers: dict,
):
    # Tourist 1 starts trip and posts locations
    now = datetime.now(timezone.utc)
    create_trip_resp = client.post(
        "/api/v1/trips",
        headers=tourist_token_headers,
        json={
            "title": "Kyoto Trails",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=2)).isoformat(),
        },
    )
    trip_id = create_trip_resp.json()["id"]
    client.post(f"/api/v1/trips/{trip_id}/start", headers=tourist_token_headers)

    # Ingest 2 locations
    client.post(
        "/api/v1/location",
        headers=tourist_token_headers,
        json={
            "trip_id": trip_id,
            "latitude": 35.0,
            "longitude": 135.0,
            "accuracy": 5.0,
            "recorded_at": (now - timedelta(minutes=2)).isoformat(),
        },
    )
    client.post(
        "/api/v1/location",
        headers=tourist_token_headers,
        json={
            "trip_id": trip_id,
            "latitude": 35.01,
            "longitude": 135.01,
            "accuracy": 5.0,
            "recorded_at": now.isoformat(),
        },
    )

    # 1. Owning tourist can view history
    res_owner = client.get(f"/api/v1/location/history/{trip_id}", headers=tourist_token_headers)
    assert res_owner.status_code == 200
    assert len(res_owner.json()) == 2

    # 2. Authority can view history
    res_auth = client.get(f"/api/v1/location/history/{trip_id}", headers=authority_token_headers)
    assert res_auth.status_code == 200
    assert len(res_auth.json()) == 2

    # 3. Unrelated tourist cannot view history
    res_other = client.get(f"/api/v1/location/history/{trip_id}", headers=tourist_2_token_headers)
    assert res_other.status_code == 403
