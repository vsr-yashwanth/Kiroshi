import pytest
import uuid
from backend.app.domain.models.incident import Incident
from backend.app.domain.models.camera import Camera
from backend.app.domain.models.enums import (
    IncidentSource,
    IncidentSeverity,
    IncidentStatus,
    CameraStatus,
    InvestigationStatus,
)


def test_camera_registration_and_proximity_search(client, authority_token_headers, tourist_token_headers):
    # 1. Authority registers CCTV camera
    cam_payload = {
        "name": "Leh Main Market Cam 01",
        "description": "Fixed 4K camera overlooking central bazaar",
        "latitude": 34.1526,
        "longitude": 77.5771,
        "coverage_radius_meters": 75.0,
        "is_simulated": True,
        "stream_url": "rtsp://simulated-cctv.kiroshi.local/leh-market-01",
        "camera_metadata": {"fov_degrees": 110, "mounting_height_m": 4.5}
    }
    res = client.post("/api/v1/cctv/cameras", json=cam_payload, headers=authority_token_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == cam_payload["name"]
    assert data["status"] == "ACTIVE"
    cam_id = data["id"]

    # 2. Tourists cannot register cameras (RBAC enforcement)
    res_tourist = client.post("/api/v1/cctv/cameras", json=cam_payload, headers=tourist_token_headers)
    assert res_tourist.status_code == 403

    # 3. Spatial Proximity Search
    res_nearby = client.get(
        "/api/v1/cctv/cameras/nearby?latitude=34.1526&longitude=77.5771&radius_meters=300",
        headers=authority_token_headers
    )
    assert res_nearby.status_code == 200
    cams = res_nearby.json()
    assert len(cams) >= 1
    assert any(c["id"] == cam_id for c in cams)


def test_scoped_cctv_investigation_on_incident(client, db_session, authority_token_headers, tourist_user):
    # 1. Create active Incident
    incident = Incident(
        tourist_id=tourist_user.id,
        source=IncidentSource.SOS,
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.DETECTED,
        latitude=34.1526,
        longitude=77.5771,
        description="Tourist triggered SOS near Leh Main Market",
    )
    db_session.add(incident)
    db_session.commit()
    db_session.refresh(incident)

    # 2. Register Camera in area
    cam = Camera(
        name="Leh Square Camera",
        status=CameraStatus.ACTIVE.value,
        location="POINT(77.5771 34.1526)",
        coverage_radius_meters=60.0,
        is_simulated=True,
    )
    db_session.add(cam)
    db_session.commit()

    # 3. Launch Scoped CCTV Investigation
    inv_payload = {
        "incident_id": str(incident.id),
        "search_radius_meters": 250.0,
        "time_window_minutes_before": 5.0,
        "time_window_minutes_after": 5.0,
    }
    res = client.post("/api/v1/cctv/investigate", json=inv_payload, headers=authority_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["incident_id"] == str(incident.id)
    assert data["status"] in ["COMPLETED", "NO_FOOTAGE_AVAILABLE"]
    assert "cameras_queried" in data
    assert "detection_results" in data

    # 4. Query Investigation by ID
    inv_id = data["id"]
    res_get = client.get(f"/api/v1/cctv/investigations/{inv_id}", headers=authority_token_headers)
    assert res_get.status_code == 200
    assert res_get.json()["id"] == inv_id
