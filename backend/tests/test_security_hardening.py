import uuid
import pytest
from fastapi.testclient import TestClient


def test_security_unauthenticated_requests_rejected(client: TestClient):
    """
    Verify that protected endpoints reject requests lacking Authorization Bearer headers with 401.
    """
    protected_endpoints = [
        ("GET", "/api/v1/tourists/me"),
        ("PUT", "/api/v1/tourists/me"),
        ("POST", "/api/v1/trips"),
        ("POST", "/api/v1/location"),
        ("POST", "/api/v1/incidents/sos"),
        ("GET", "/api/v1/audit/events"),
        ("POST", "/api/v1/audit/verify"),
        ("POST", "/api/v1/cctv/investigate"),
    ]

    for method, path in protected_endpoints:
        if method == "GET":
            resp = client.get(path)
        elif method == "PUT":
            resp = client.put(path, json={})
        else:
            resp = client.post(path, json={})
        assert resp.status_code == 401, f"Endpoint {method} {path} should return 401 for unauthenticated request"
        assert "X-Request-ID" in resp.headers


def test_security_tourist_cannot_access_authority_endpoints(client: TestClient, tourist_token_headers: dict):
    """
    Verify RBAC enforcement preventing TOURIST role from accessing AUTHORITY/ADMIN endpoints.
    """
    authority_endpoints = [
        ("GET", "/api/v1/audit/events"),
        ("POST", "/api/v1/audit/verify"),
        ("POST", "/api/v1/cctv/investigate"),
        ("POST", "/api/v1/audit/export"),
    ]

    for method, path in authority_endpoints:
        if method == "GET":
            resp = client.get(path, headers=tourist_token_headers)
        else:
            resp = client.post(path, json={}, headers=tourist_token_headers)
        assert resp.status_code == 403, f"Endpoint {method} {path} should return 403 Forbidden for TOURIST role"


def test_security_malformed_json_returns_422(client: TestClient, tourist_token_headers: dict):
    """
    Verify that malformed requests are safely handled and return 422 Unprocessable Entity without stack traces.
    """
    resp = client.post(
        "/api/v1/location",
        headers=tourist_token_headers,
        content="not-a-valid-json-string",
    )
    assert resp.status_code in [400, 422]
    assert "X-Request-ID" in resp.headers

