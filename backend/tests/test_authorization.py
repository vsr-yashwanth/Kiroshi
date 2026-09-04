import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta


def test_unauthenticated_request_fails(client: TestClient):
    response = client.get("/api/v1/tourists/me")
    assert response.status_code == 401


def test_tourist_cannot_inspect_other_tourist_profile(
    client: TestClient,
    tourist_user_2,
    tourist_token_headers,
):
    # Tourist 1 attempts to inspect Tourist 2's profile by ID
    response = client.get(
        f"/api/v1/tourists/{tourist_user_2.id}",
        headers=tourist_token_headers,
    )
    assert response.status_code == 403
    assert "sufficient permissions" in response.json()["detail"]


def test_tourist_cannot_access_other_tourist_trip(
    client: TestClient,
    tourist_token_headers,
    tourist_2_token_headers,
):
    # Tourist 1 creates a trip
    start_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    end_time = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()

    create_res = client.post(
        "/api/v1/trips",
        headers=tourist_token_headers,
        json={
            "title": "Private Adventure",
            "start_date": start_time,
            "end_date": end_time,
        },
    )
    assert create_res.status_code == 201
    trip_id = create_res.json()["id"]

    # Tourist 2 attempts to fetch Tourist 1's trip
    fetch_res = client.get(
        f"/api/v1/trips/{trip_id}",
        headers=tourist_2_token_headers,
    )
    assert fetch_res.status_code == 403
    assert "not authorized" in fetch_res.json()["detail"]

    # Tourist 2 attempts to start Tourist 1's trip
    start_res = client.post(
        f"/api/v1/trips/{trip_id}/start",
        headers=tourist_2_token_headers,
    )
    assert start_res.status_code == 403
