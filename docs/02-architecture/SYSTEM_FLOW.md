# System Flow — KIROSHI v0.2

> Status: IMPLEMENTED (v0.2)

---

## 1. Primary v0.1 Core Onboarding & Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor Tourist as Tourist User
    participant App as Tourist App / API Client
    participant Backend as FastAPI Backend
    participant DB as Relational Database
    actor Authority as Tourism Authority
    participant Dash as Authority Dashboard

    %% Registration & Login
    Note over Tourist, DB: 1. Onboarding & Authentication
    Tourist->>App: Register (Email, Password, Name, Role=TOURIST)
    App->>Backend: POST /api/v1/auth/register
    Backend->>DB: Check unique email & insert User (hashed pw)
    DB-->>Backend: User created
    Backend-->>App: 201 Created (User DTO)

    Tourist->>App: Login (Email, Password)
    App->>Backend: POST /api/v1/auth/login
    Backend->>DB: Fetch user by email
    Backend->>Backend: Verify bcrypt hash & generate JWT
    Backend-->>App: 200 OK (access_token, token_type=bearer)

    %% Profile Setup
    Note over Tourist, DB: 2. Tourist Profile Setup
    Tourist->>App: Submit Profile (Emergency contacts, Consent)
    App->>Backend: PUT /api/v1/tourists/me (Bearer Token)
    Backend->>DB: Upsert TouristProfile for current user
    DB-->>Backend: Profile saved
    Backend-->>App: 200 OK (TouristProfile DTO)

    %% Trip & Itinerary
    Note over Tourist, DB: 3. Trip Lifecycle
    Tourist->>App: Create Trip with Itinerary Waypoints
    App->>Backend: POST /api/v1/trips (Title, Dates, Waypoints)
    Backend->>DB: Insert Trip (status=PLANNED) + Itinerary records
    DB-->>Backend: Trip & Itinerary persisted
    Backend-->>App: 201 Created (Trip DTO)

    Tourist->>App: Press "Start Trip"
    App->>Backend: POST /api/v1/trips/{id}/start
    Backend->>Backend: Verify trip ownership & valid transition
    Backend->>DB: Update Trip (status=ACTIVE)
    DB-->>Backend: Updated
    Backend-->>App: 200 OK (status=ACTIVE)
```

---

## 2. v0.2 Real-Time Geospatial & Geofencing Pipeline

The v0.2 architecture establishes real-time telemetry streaming from tourist mobile devices into PostGIS spatial storage, evaluates polygon containment, and fans out low-latency WebSockets to authority dashboards:

```mermaid
sequenceDiagram
    autonumber
    actor Tourist as Tourist (Mobile)
    participant Mobile as Flutter App (Geolocator)
    participant Backend as FastAPI Location Service
    participant PostGIS as PostgreSQL 16 + PostGIS 3.4
    participant WSManager as WebSocket Connection Manager
    actor Authority as Authority Officer
    participant Dash as Authority Dashboard

    Note over Authority, Dash: 1. Authority Live Monitoring Session
    Authority->>Dash: Open Live Geospatial Map
    Dash->>Backend: Connect WebSocket /api/v1/ws/authority?token=JWT
    Backend->>Backend: Validate JWT & verify role is AUTHORITY or ADMIN
    Backend->>WSManager: Register active WebSocket connection
    Backend->>PostGIS: Fetch active tourists & latest location snapshots
    PostGIS-->>Backend: Current positions & zone states
    Backend-->>Dash: Send initial "snapshot" message with active positions

    Note over Tourist, Dash: 2. Real-Time Telemetry & Geofence Pipeline
    Mobile->>Mobile: Device GPS fix acquired (lat, lon, accuracy, speed)
    Mobile->>Mobile: Distance filter check (>10m movement)
    Mobile->>Backend: POST /api/v1/location (trip_id, lat, lon, recorded_at, accuracy)
    
    Backend->>Backend: 1. Authenticate user via JWT Bearer
    Backend->>Backend: 2. Verify tourist_id matches token (IDOR prevention)
    Backend->>Backend: 3. Validate coordinates (-90..90, -180..180)
    Backend->>Backend: 4. Validate accuracy (>0m and <=200m)
    Backend->>Backend: 5. Verify trip ownership and status == ACTIVE
    Backend->>Backend: 6. Check clock skew (|now - recorded_at| <= 300s)

    Backend->>PostGIS: Persist LocationEvent (Point SRID 4326, GIST indexed)
    
    Backend->>PostGIS: Spatial query active GeoZones: ST_Covers(geometry, ST_SetSRID(ST_MakePoint(lon, lat), 4326))
    PostGIS-->>Backend: Containing zones matching coordinates

    Backend->>Backend: Evaluate state transitions against TouristZoneState
    alt Tourist entered new zone (outside -> inside)
        Backend->>PostGIS: Insert TouristZoneState (is_inside = True)
        Backend->>PostGIS: Record ZoneEvent (event_type = ENTER)
        Backend->>WSManager: Broadcast zone_event {event_type: "ENTER", zone_name, severity}
    else Tourist left previous zone (inside -> outside)
        Backend->>PostGIS: Update TouristZoneState (is_inside = False)
        Backend->>PostGIS: Record ZoneEvent (event_type = EXIT)
        Backend->>WSManager: Broadcast zone_event {event_type: "EXIT", zone_name, severity}
    else Tourist remains inside (inside -> inside)
        Backend->>Backend: No duplicate event emitted
    end

    Backend->>WSManager: Broadcast location_update {tourist_id, trip_id, lat, lon, freshness: "LIVE"}
    WSManager-->>Dash: Push real-time telemetry frame
    Dash->>Dash: Animate tourist marker & update breadcrumb route trail
    Backend-->>Mobile: 201 Created (LocationEvent DTO + triggered events)
```

---

## 3. Geofence State Transition Truth Table

To eliminate alert spamming, the transition engine enforces strict edge-triggered events:

| Previous State | Current Containment | State Change? | Event Emitted | Audit Record Created |
|---|---|---|---|---|
| `OUTSIDE` (or none) | `INSIDE` | Yes | `ENTER` | Yes |
| `INSIDE` | `INSIDE` | No | *None* | No |
| `INSIDE` | `OUTSIDE` | Yes | `EXIT` | Yes |
| `OUTSIDE` | `OUTSIDE` | No | *None* | No |

---

## 4. Location Freshness Classification

Telemetry displayed on the Authority Dashboard is classified dynamically based on `recorded_at` relative to current server time:

| Freshness Level | Age Threshold | UI Visualization | Operational Status |
|---|---|---|---|
| **`LIVE`** | `< 60 seconds` | Emerald pulse marker | Active real-time tracking |
| **`RECENT`** | `60s – 300s (5 min)` | Blue marker | Normal GPS intermittent ping |
| **`STALE`** | `300s – 1800s (30 min)`| Amber warning marker | Possible signal loss or battery-saving |
| **`UNKNOWN`** | `> 1800s (30 min)` | Muted gray marker | Disconnected / Stale journey |

---

## 5. Security & Isolation Invariants

- **Token Bound**: `tourist_id` is never read from untrusted client payloads; it is strictly derived from the verified JWT `sub` claim.
- **Trip Isolation**: Location points cannot be recorded against trips owned by other tourists or trips not currently in `ACTIVE` state.
- **WebSocket RBAC**: WebSocket connections to `/api/v1/ws/authority` require valid authentication and are restricted to users with `AUTHORITY` or `ADMIN` roles. Unauthorized clients receive close code `1008 Policy Violation`.
- **Sanitized Telemetry**: WebSocket location frames broadcast minimal operational payloads (coordinates, accuracy, timestamp, trip ID) without broadcasting sensitive identity hashes or medical notes.

---

## 6. v0.4 Emergency Response & Incident Lifecycle Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor Tourist as Tourist Mobile App
    participant API as FastAPI /api/v1/incidents
    participant DB as PostgreSQL (Incidents & Events)
    participant WS as WebSocket ConnectionManager
    actor Authority as Authority Dashboard
    actor Responder as Field Responder

    Tourist->>API: POST /api/v1/incidents/sos (idempotency_key, coordinates)
    API->>DB: Check idempotency & create Incident (status=DETECTED)
    API->>DB: Append IncidentEvent (INCIDENT_CREATED)
    API->>WS: Broadcast INCIDENT_CREATED
    WS-->>Authority: Display incoming distress beacon

    Authority->>API: POST /api/v1/incidents/{id}/transition (to_status=VERIFYING)
    API->>DB: Validate state transition & append event
    API->>WS: Broadcast INCIDENT_STATUS_CHANGED

    Authority->>API: POST /api/v1/incidents/{id}/transition (to_status=VERIFIED)
    API->>DB: Validate state transition & append event
    API->>WS: Broadcast INCIDENT_STATUS_CHANGED

    Authority->>API: POST /api/v1/incidents/{id}/assign (responder_id)
    API->>DB: Persist IncidentAssignment & advance to ASSIGNED
    API->>DB: In-App Notification -> Responder
    API->>WS: Broadcast INCIDENT_ASSIGNED

    Responder->>API: POST /api/v1/incidents/{id}/transition (to_status=RESPONDING)
    API->>DB: Validate state transition & append event
    API->>WS: Broadcast INCIDENT_STATUS_CHANGED

    Responder->>API: POST /api/v1/incidents/{id}/transition (to_status=RESOLVED, notes)
    API->>DB: Validate state transition & append event
    API->>WS: Broadcast INCIDENT_STATUS_CHANGED

    Authority->>API: POST /api/v1/incidents/{id}/transition (to_status=CLOSED)
    API->>DB: Move to terminal state & append event
    API->>WS: Broadcast INCIDENT_STATUS_CHANGED
```

