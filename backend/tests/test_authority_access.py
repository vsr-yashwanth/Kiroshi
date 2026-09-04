import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta


def test_authority_can_list_tourists(
    client: TestClient,
    tourist_user,
    tourist_user_2,
    authority_token_headers,
):
    response = client.get("/api/v1/tourists", headers=authority_token_headers)
    assert response.status_code == 200
    tourists = response.json()
    assert len(tourists) >= 2
    emails = [t["email"] for t in tourists]
    assert tourist_user.email in emails
    assert tourist_user_2.email in emails


def test_authority_can_inspect_tourist_profile(
    client: TestClient,
    tourist_user,
    authority_token_headers,
):
    response = client.get(
        f"/api/v1/tourists/{tourist_user.id}",
        headers=authority_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nationality"] == "Canadian"
    assert data["emergency_contact_name"] == "Bob Traveler"


def test_authority_can_view_all_active_trips(
    client: TestClient,
    tourist_token_headers,
    authority_token_headers,
):
    # Tourist creates and starts a trip
    start_time = datetime.now(timezone.utc).isoformat()
    end_time = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

    create_res = client.post(
        "/api/v1/trips",
        headers=tourist_token_headers,
        json={
            "title": "Mountain Expedition",
            "start_date": start_time,
            "end_date": end_time,
        },
    )
    assert create_res.status_code == 201
    trip_id = create_res.json()["id"]

    start_res = client.post(
        f"/api/v1/trips/{trip_id}/start",
        headers=tourist_token_headers,
    )
    assert start_res.status_code == 200

    # Authority queries active trips
    auth_res = client.get(
        "/api/v1/trips?status=ACTIVE",
        headers=authority_token_headers,
    )
    assert auth_res.status_code == 200
    trips = auth_res.json()
    assert any(t["id"] == trip_id for t in trips)
