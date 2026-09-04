# System Flow — KIROSHI v0.1

> Status: IMPLEMENTED (v0.1)

---

## 1. Primary v0.1 End-to-End Workflow

The primary end-to-end flow connects the tourist onboarding lifecycle with authority operational oversight:

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

    %% Authority Inspection
    Note over Authority, DB: 4. Authority Operational Oversight
    Authority->>Dash: Login (Email, Password, Role=AUTHORITY)
    Dash->>Backend: POST /api/v1/auth/login
    Backend-->>Dash: 200 OK (access_token)

    Dash->>Backend: GET /api/v1/trips?status=ACTIVE
    Backend->>Backend: Validate user has AUTHORITY or ADMIN role
    Backend->>DB: Query all trips with status=ACTIVE
    DB-->>Backend: Active trips list
    Backend-->>Dash: 200 OK (Active trips with tourist summary)

    Authority->>Dash: Inspect specific tourist details
    Dash->>Backend: GET /api/v1/tourists/{id}
    Backend->>Backend: Validate AUTHORITY permissions
    Backend->>DB: Query tourist profile & emergency contacts
    DB-->>Backend: Tourist profile
    Backend-->>Dash: 200 OK (Full profile details)
```

---

## 2. Error & Security Flow (Cross-User Isolation)

To verify robust server-side authorization:
- If **Tourist A** requests `GET /api/v1/tourists/{Tourist_B_id}`, the backend returns **403 Forbidden** (Role `TOURIST` is not permitted to query arbitrary user profiles).
- If **Tourist A** attempts `POST /api/v1/trips/{Tourist_B_trip_id}/start`, the backend returns **403 Forbidden** (Trip does not belong to the requesting user).
- If an unauthenticated client requests any protected resource without a valid Bearer token, the backend returns **401 Unauthorized**.
