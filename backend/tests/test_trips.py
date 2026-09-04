import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta


def test_create_and_get_trip_with_itineraries(client: TestClient, tourist_token_headers):
    start = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    end = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    payload = {
        "title": "Himalayan Ridge Trek",
        "description": "5-day high altitude trek",
        "start_date": start,
        "end_date": end,
        "itineraries": [
            {
                "destination_name": "Manali Base Camp",
                "latitude": 32.2432,
                "longitude": 77.1892,
                "sequence_order": 1,
            },
            {
                "destination_name": "Solang Valley Pass",
                "latitude": 32.3167,
                "longitude": 77.1578,
                "sequence_order": 2,
            },
        ],
    }

    create_res = client.post("/api/v1/trips", headers=tourist_token_headers, json=payload)
    assert create_res.status_code == 201
    trip = create_res.json()
    assert trip["title"] == "Himalayan Ridge Trek"
    assert trip["status"] == "PLANNED"
    assert len(trip["itineraries"]) == 2
    assert trip["itineraries"][0]["destination_name"] == "Manali Base Camp"

    # Fetch trip by ID
    trip_id = trip["id"]
    get_res = client.get(f"/api/v1/trips/{trip_id}", headers=tourist_token_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == trip_id


def test_trip_lifecycle_state_transitions(client: TestClient, tourist_token_headers):
    start = datetime.now(timezone.utc).isoformat()
    end = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    create_res = client.post(
        "/api/v1/trips",
        headers=tourist_token_headers,
        json={"title": "Lifecycle Test", "start_date": start, "end_date": end},
    )
    trip_id = create_res.json()["id"]

    # 1. Attempt invalid transition: stop before start
    stop_early_res = client.post(f"/api/v1/trips/{trip_id}/stop", headers=tourist_token_headers)
    assert stop_early_res.status_code == 400
    assert "Cannot transition from PLANNED to COMPLETED" in stop_early_res.json()["detail"]

    # 2. Start trip: PLANNED -> ACTIVE
    start_res = client.post(f"/api/v1/trips/{trip_id}/start", headers=tourist_token_headers)
    assert start_res.status_code == 200
    assert start_res.json()["status"] == "ACTIVE"

    # 3. Attempt starting again
    start_again_res = client.post(f"/api/v1/trips/{trip_id}/start", headers=tourist_token_headers)
    assert start_again_res.status_code == 400
    assert "Cannot transition from ACTIVE to ACTIVE" in start_again_res.json()["detail"]

    # 4. Stop trip: ACTIVE -> COMPLETED
    stop_res = client.post(f"/api/v1/trips/{trip_id}/stop", headers=tourist_token_headers)
    assert stop_res.status_code == 200
    assert stop_res.json()["status"] == "COMPLETED"
