# API Specification — KIROSHI v0.3

> Status: IMPLEMENTED (v0.3) | Base Path: `/api/v1`

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
      "version": "0.2.0"
    }
    ```

---

## 5. Location & Telemetry Endpoints (v0.2)

### `POST /api/v1/location`
Ingests a GPS location fix for an active trip. Performs validation, PostGIS persistence, geofence evaluation, and real-time WebSocket broadcast.

- **Access**: Authenticated (`TOURIST`)
- **Request Body**:
  ```json
  {
    "trip_id": "7b8971f4-3450-424a-9b16-562aef768222",
    "latitude": 32.2432,
    "longitude": 77.1892,
    "altitude": 2050.5,
    "accuracy": 8.0,
    "speed": 1.2,
    "bearing": 180.0,
    "recorded_at": "2026-09-04T10:15:30Z"
  }
  ```
- **Responses**:
  - `201 Created`: Location ingested with triggered geofence events.
    ```json
    {
      "id": "9f2a4128-...",
      "tourist_id": "c1f72922-...",
      "trip_id": "7b8971f4-...",
      "latitude": 32.2432,
      "longitude": 77.1892,
      "altitude": 2050.5,
      "accuracy": 8.0,
      "speed": 1.2,
      "bearing": 180.0,
      "recorded_at": "2026-09-04T10:15:30Z",
      "received_at": "2026-09-04T10:15:31Z",
      "triggered_events": [
        {
          "event_type": "ENTER",
          "zone_name": "Solang Avalanche Basin",
          "zone_type": "HIGH_RISK"
        }
      ]
    }
    ```
  - `400 Bad Request`: Validation failure (out-of-range coordinates, invalid accuracy, clock skew > 300s, or trip not in `ACTIVE` state).
  - `403 Forbidden`: Trip does not belong to the authenticated tourist.
  - `404 Not Found`: Trip does not exist.

### `GET /api/v1/location/history/{trip_id}`
Retrieves chronologically ordered GPS breadcrumb trail for a specific trip.

- **Access**: Trip Owner (`TOURIST`) or `AUTHORITY` / `ADMIN`.
- **Query Parameters**:
  - `limit`: Integer (default 500, max 2000).
- **Responses**:
  - `200 OK`: List of `LocationEvent` DTOs.
  - `403 Forbidden`: Trip belongs to another tourist.

### `GET /api/v1/location/active`
Retrieves latest known location and freshness status for all currently active trips.

- **Access**: `AUTHORITY` or `ADMIN`.
- **Responses**:
  - `200 OK`: List of active tourist telemetry records.

---

## 6. GeoZone Management Endpoints (v0.2)

### `GET /api/v1/zones`
Lists all active geofence zones.

- **Access**: Authenticated (`TOURIST`, `AUTHORITY`, `ADMIN`).
- **Responses**:
  - `200 OK`: Array of `GeoZone` objects with geometry vertex coordinates.

### `POST /api/v1/zones`
Creates a new geofence polygon zone.

- **Access**: `AUTHORITY` or `ADMIN`.
- **Request Body**:
  ```json
  {
    "name": "Solang Avalanche Basin",
    "zone_type": "HIGH_RISK",
    "coordinates": [
      [32.2400, 77.1850],
      [32.2500, 77.1850],
      [32.2500, 77.1950],
      [32.2400, 77.1950],
      [32.2400, 77.1850]
    ],
    "description": "Active avalanche slide path during winter/spring months."
  }
  ```
- **Responses**:
  - `201 Created`: GeoZone created and indexed.
  - `400 Bad Request`: Invalid polygon geometry (<3 vertices, self-intersecting, or invalid coordinate ranges).
  - `403 Forbidden`: Insufficient authority permissions.

### `GET /api/v1/zones/events`
Retrieves recent geofence crossing audit log (`ENTER` and `EXIT` events).

- **Access**: `AUTHORITY` or `ADMIN`.
- **Query Parameters**:
  - `limit`: Integer (default 50).
- **Responses**:
  - `200 OK`: List of `ZoneEvent` records.

### `DELETE /api/v1/zones/{id}`
Deactivates or deletes a geofence zone.

- **Access**: `AUTHORITY` or `ADMIN`.
- **Responses**:
  - `200 OK`: `{"message": "Zone deleted successfully"}`
  - `404 Not Found`: Zone does not exist.

---

## 7. Real-Time Streaming (v0.2)

### `WebSocket /api/v1/ws/authority`
Full-duplex real-time telemetry and geofence alert stream for authority dashboards.

- **Access**: Authenticated via Query Parameter `?token=<JWT_TOKEN>` (`AUTHORITY` or `ADMIN`).
- **Events Streamed**:
  - `INITIAL_SNAPSHOT`: Initial state hydration of all active tourists upon connect.
  - `LOCATION_UPDATE`: Real-time GPS movement, freshness indicator, and active `risk_level` & `risk_score`.
  - `ZONE_ENTER` / `ZONE_EXIT`: Immediate geofence crossing alerts.
  - `RISK_UPDATE`: Real-time explainable risk assessment payload (when subscribed via `?subscribe_risk=true` or client command `SUBSCRIBE_RISK`).
  - `PONG`: Response to client `PING` keepalive.

---

## 8. Risk Assessment Endpoints (v0.3)

### `GET /api/v1/risk/current/{tourist_id}`
Returns the most recent persisted explainable risk assessment for a tourist.

- **Access**: The tourist themselves (`TOURIST` with matching ID), `AUTHORITY`, or `ADMIN`.
- **Responses**:
  - `200 OK`:
    ```json
    {
      "id": "7b8c2d1e-...",
      "tourist_id": "c1f72922-...",
      "trip_id": "e4a219b0-...",
      "location_event_id": "f5c90a12-...",
      "risk_score": 0.45,
      "risk_level": "MEDIUM",
      "confidence": 0.85,
      "contributing_signals": [
        {
          "signal_type": "HIGH_RISK_ZONE",
          "score": 1.0,
          "weight": 0.45,
          "contribution": 0.45,
          "raw_value": true,
          "unit": "boolean",
          "description": "Active inside high-risk hazard perimeter"
        }
      ],
      "explanation": "Risk evaluated as MEDIUM (0.45): Active location inside a high-risk safety perimeter.",
      "recommended_action": "REVIEW",
      "model_version": "v0.3-rule-engine",
      "created_at": "2026-09-04T12:00:00Z"
    }
    ```
  - `403 Forbidden`: Cross-tourist unauthorized access.
  - `404 Not Found`: No risk evaluation found for tourist.

### `GET /api/v1/risk/history/{trip_id}`
Returns the chronological evaluation history of risk scores, signals, and explanations across a trip.

- **Access**: The trip owner tourist, `AUTHORITY`, or `ADMIN`.
- **Query Parameters**:
  - `limit`: Integer (default 100, max 1000).
- **Responses**:
  - `200 OK`: Array of `RiskAssessmentResponse` records sorted by `created_at DESC`.
  - `403 Forbidden`: Unauthorized tourist access.
  - `404 Not Found`: Trip not found.

### `GET /api/v1/risk/active`
Returns the active fleet risk snapshot across all currently active tourist journeys.

- **Access**: `AUTHORITY` or `ADMIN`.
- **Responses**:
  - `200 OK`: Array of `LiveTouristRiskSnapshot` objects containing tourist ID, name, trip ID, trip title, latest risk score, level, confidence, and timestamp.
  - `403 Forbidden`: Tourist role forbidden.

