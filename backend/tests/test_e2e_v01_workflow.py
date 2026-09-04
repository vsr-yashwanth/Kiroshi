import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from backend.app.domain.models.enums import UserRole


def test_complete_v01_vertical_slice_workflow(client: TestClient):
    """
    Validates the complete v0.1 engineering contract workflow:
    Tourist Register -> Login -> Profile -> Create Trip -> Start Trip
    -> Authority Login -> View Tourist -> View Active Trip
    """

    # 1. Tourist Register
    tourist_reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "sarah.connor@example.com",
            "password": "Terminator123!",
            "full_name": "Sarah Connor",
            "phone_number": "+18005550199",
            "role": "TOURIST",
        },
    )
    assert tourist_reg_res.status_code == 201
    tourist_id = tourist_reg_res.json()["id"]

    # 2. Tourist Login
    tourist_login_res = client.post(
        "/api/v1/auth/login",
        json={
            "username": "sarah.connor@example.com",
            "password": "Terminator123!",
        },
    )
    assert tourist_login_res.status_code == 200
    tourist_token = tourist_login_res.json()["access_token"]
    tourist_headers = {"Authorization": f"Bearer {tourist_token}"}

    # 3. Tourist Profile Setup
    profile_update_res = client.put(
        "/api/v1/tourists/me",
        headers=tourist_headers,
        json={
            "nationality": "American",
            "emergency_contact_name": "John Connor",
            "emergency_contact_phone": "+18005550200",
            "medical_notes": "No severe allergies; high stamina.",
            "consent_given": True,
        },
    )
    assert profile_update_res.status_code == 200
    profile_data = profile_update_res.json()
    assert profile_data["emergency_contact_name"] == "John Connor"
    assert profile_data["consent_given"] is True

    # 4. Create Trip with Waypoints
    now = datetime.now(timezone.utc)
    trip_create_res = client.post(
        "/api/v1/trips",
        headers=tourist_headers,
        json={
            "title": "High Desert Recon",
            "description": "Exploration of Mohave mountain pass",
            "start_date": (now + timedelta(hours=1)).isoformat(),
            "end_date": (now + timedelta(days=3)).isoformat(),
            "itineraries": [
                {
                    "destination_name": "Desert Checkpoint Alpha",
                    "latitude": 34.1378,
                    "longitude": -116.0543,
                    "sequence_order": 1,
                },
                {
                    "destination_name": "Observation Ridge Beta",
                    "latitude": 34.2541,
                    "longitude": -116.1892,
                    "sequence_order": 2,
                },
            ],
        },
    )
    assert trip_create_res.status_code == 201
    trip_id = trip_create_res.json()["id"]
    assert trip_create_res.json()["status"] == "PLANNED"
    assert len(trip_create_res.json()["itineraries"]) == 2

    # 5. Start Trip
    start_trip_res = client.post(
        f"/api/v1/trips/{trip_id}/start",
        headers=tourist_headers,
    )
    assert start_trip_res.status_code == 200
    assert start_trip_res.json()["status"] == "ACTIVE"

    # 6. Authority Register & Login
    auth_reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "chief.director@tourism.gov",
            "password": "AuthoritySuperSecure123!",
            "full_name": "Director Vance",
            "phone_number": "+18005550001",
            "role": "AUTHORITY",
        },
    )
    assert auth_reg_res.status_code == 201

    auth_login_res = client.post(
        "/api/v1/auth/login",
        json={
            "username": "chief.director@tourism.gov",
            "password": "AuthoritySuperSecure123!",
        },
    )
    assert auth_login_res.status_code == 200
    authority_token = auth_login_res.json()["access_token"]
    authority_headers = {"Authorization": f"Bearer {authority_token}"}

    # 7. Authority Lists Tourists
    tourist_list_res = client.get(
        "/api/v1/tourists",
        headers=authority_headers,
    )
    assert tourist_list_res.status_code == 200
    tourist_list = tourist_list_res.json()
    assert any(t["id"] == tourist_id for t in tourist_list)

    # 8. Authority Views Tourist Details
    tourist_inspect_res = client.get(
        f"/api/v1/tourists/{tourist_id}",
        headers=authority_headers,
    )
    assert tourist_inspect_res.status_code == 200
    inspected_profile = tourist_inspect_res.json()
    assert inspected_profile["emergency_contact_name"] == "John Connor"
    assert inspected_profile["medical_notes"] == "No severe allergies; high stamina."

    # 9. Authority Views Active Trips
    active_trips_res = client.get(
        "/api/v1/trips?status=ACTIVE",
        headers=authority_headers,
    )
    assert active_trips_res.status_code == 200
    active_trips = active_trips_res.json()
    matched_trip = next((t for t in active_trips if t["id"] == trip_id), None)
    assert matched_trip is not None
    assert matched_trip["status"] == "ACTIVE"
    assert len(matched_trip["itineraries"]) == 2
    assert matched_trip["itineraries"][0]["destination_name"] == "Desert Checkpoint Alpha"
