import pytest
from fastapi.testclient import TestClient


def test_register_user_success(client: TestClient):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newtourist@example.com",
            "password": "StrongPassword123!",
            "full_name": "New Traveler",
            "phone_number": "+1234567890",
            "role": "TOURIST",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newtourist@example.com"
    assert data["full_name"] == "New Traveler"
    assert data["role"] == "TOURIST"
    assert "id" in data


def test_register_duplicate_email_fails(client: TestClient, tourist_user):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": tourist_user.email,
            "password": "AnotherPassword123!",
            "full_name": "Clone User",
            "role": "TOURIST",
        },
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_login_success(client: TestClient, tourist_user):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": tourist_user.email,
            "password": "Password123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == tourist_user.email


def test_login_wrong_password_fails(client: TestClient, tourist_user):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": tourist_user.email,
            "password": "WrongPassword!",
        },
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user_fails(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "ghost@example.com",
            "password": "AnyPassword123!",
        },
    )
    assert response.status_code == 401


def test_logout(client: TestClient, tourist_token_headers):
    response = client.post(
        "/api/v1/auth/logout",
        headers=tourist_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"
