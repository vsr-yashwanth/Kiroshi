# API Specification — KIROSHI v0.1

> Status: IMPLEMENTED (v0.1) | Base Path: `/api/v1`

---

## 1. Authentication Endpoints

### `POST /api/v1/auth/register`
Creates a new user account.

- **Access**: Public
- **Request Body**:
  ```json
  {
    "email": "tourist@example.com",
    "password": "SecurePassword123!",
    "full_name": "Jane Doe",
    "phone_number": "+15551234567",
    "role": "TOURIST"
  }
  ```
- **Responses**:
  - `201 Created`: User successfully registered.
  - `400 Bad Request`: Validation error or duplicate email.

### `POST /api/v1/auth/login`
Authenticates user credentials and returns a JWT Bearer token.

- **Access**: Public
- **Request Body (JSON or x-www-form-urlencoded)**:
  ```json
  {
    "username": "tourist@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Responses**:
  - `200 OK`:
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1Ni...",
      "token_type": "bearer",
      "user": {
        "id": "c1f72922-...",
        "email": "tourist@example.com",
        "full_name": "Jane Doe",
        "role": "TOURIST"
      }
    }
    ```
  - `401 Unauthorized`: Invalid credentials.

### `POST /api/v1/auth/logout`
Logs out current session.
- **Access**: Authenticated (Bearer Token)
- **Responses**:
  - `200 OK`: `{"message": "Logged out successfully"}`

---

## 2. Tourist Profile Endpoints

### `GET /api/v1/tourists/me`
Retrieves the authenticated tourist's profile.
- **Access**: Authenticated (`TOURIST`)
- **Responses**:
  - `200 OK`: Profile details or null if not yet created.

### `PUT /api/v1/tourists/me`
Creates or updates the authenticated tourist's profile.
- **Access**: Authenticated (`TOURIST`)
- **Request Body**:
  ```json
  {
    "nationality": "Canadian",
    "emergency_contact_name": "John Doe",
    "emergency_contact_phone": "+15559876543",
    "medical_notes": "Allergic to penicillin",
    "consent_given": true
  }
  ```
- **Responses**:
  - `200 OK`: Updated profile.

### `GET /api/v1/tourists/{id}`
Inspects a specific tourist profile.
- **Access**: Authority only (`AUTHORITY`, `ADMIN`)
- **Responses**:
  - `200 OK`: Profile details.
  - `403 Forbidden`: Requesting user is not an authority.
  - `404 Not Found`: Profile does not exist.

---

## 3. Trip Management Endpoints

### `GET /api/v1/trips`
Lists trips.
- **Access**: Authenticated
- **Behavior**:
  - For `TOURIST`: Returns only trips owned by the authenticated tourist.
  - For `AUTHORITY` / `ADMIN`: Returns all trips across all tourists (supports `?status=ACTIVE` filter).
- **Responses**:
  - `200 OK`: List of trip objects.

### `POST /api/v1/trips`
Creates a new trip with planned itinerary waypoints.
- **Access**: Authenticated (`TOURIST`, `ADMIN`)
- **Request Body**:
  ```json
  {
    "title": "Himalayan Ridge Trek",
    "description": "5-day trek from Manali to Solang Valley",
    "start_date": "2026-10-01T08:00:00Z",
    "end_date": "2026-10-06T18:00:00Z",
    "itineraries": [
      {
        "destination_name": "Basecamp Manali",
        "planned_arrival": "2026-10-01T08:00:00Z",
        "planned_departure": "2026-10-01T12:00:00Z",
        "latitude": 32.2432,
        "longitude": 77.1892,
        "sequence_order": 1
      },
      {
        "destination_name": "Solang Ridge Camp",
        "planned_arrival": "2026-10-02T16:00:00Z",
        "planned_departure": "2026-10-03T09:00:00Z",
        "latitude": 32.3167,
        "longitude": 77.1578,
        "sequence_order": 2
      }
    ]
  }
  ```
- **Responses**:
  - `201 Created`: Trip created with nested itineraries.

### `GET /api/v1/trips/{id}`
Retrieves a specific trip by UUID.
- **Access**: Trip Owner (`TOURIST`) or `AUTHORITY` / `ADMIN`.
- **Responses**:
  - `200 OK`: Trip details.
  - `403 Forbidden`: Trip belongs to another tourist.
  - `404 Not Found`: Trip not found.

### `PATCH /api/v1/trips/{id}`
Updates trip details.
- **Access**: Trip Owner.

### `POST /api/v1/trips/{id}/start`
Transitions a trip from `PLANNED` to `ACTIVE`.
- **Access**: Trip Owner.
- **Responses**:
  - `200 OK`: Trip status updated to `ACTIVE`.
  - `400 Bad Request`: Invalid state transition (e.g. trip already `COMPLETED`).
  - `403 Forbidden`: Not trip owner.

### `POST /api/v1/trips/{id}/stop`
Transitions a trip from `ACTIVE` to `COMPLETED`.
- **Access**: Trip Owner or `AUTHORITY`.
- **Responses**:
  - `200 OK`: Trip status updated to `COMPLETED`.

---

## 4. Operational Endpoints

### `GET /api/v1/health`
Performs system health check including database connectivity.
- **Access**: Public
- **Responses**:
  - `200 OK`:
    ```json
    {
      "status": "healthy",
      "environment": "development",
      "database": "connected",
      "version": "0.1.0"
    }
    ```
