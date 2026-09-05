# System Flow — KIROSHI v0.7

> Status: IMPLEMENTED (v0.7 Advanced Audit & Trust)

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

```mermaid
sequenceDiagram
    autonumber
    actor Tourist as Tourist Mobile App
    participant API as FastAPI /api/v1/locations
    participant PostGIS as PostgreSQL / PostGIS
    participant Risk as Risk Assessment Engine
    participant WS as WebSocket ConnectionManager
    actor Authority as Authority Dashboard

    Tourist->>API: POST /api/v1/locations (lat, lon, accuracy, speed)
    API->>PostGIS: ST_SetSRID(ST_MakePoint(lon, lat), 4326)
    API->>PostGIS: ST_Contains(geo_zones.polygon, point)
    PostGIS-->>API: Active Geofence Zones (Safety, Warning, Danger)
    API->>Risk: Calculate Risk Score (Geofence + Profile + Velocity)
    Risk-->>API: Risk Assessment Result
    API->>WS: Broadcast sanitized location & risk payload
    WS-->>Authority: Live Map Update
    API-->>Tourist: 201 Created (Location Point + Zone Warnings)
```

---

## 3. v0.4 Emergency Response & Incident Lifecycle Pipeline

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

---

## 4. v0.7 Advanced Audit & Cryptographic Trust Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor Actor as Authenticated User (Tourist / Responder / Admin)
    participant API as FastAPI Endpoint Layer
    participant Service as Business Domain Service
    participant AuditSvc as AuditService & Engine
    participant Hasher as AuditHasher (SHA-256)
    participant DB as PostgreSQL (audit_events Table)
    participant Verifier as AuditChainVerifier
    participant Anchor as TrustAnchor Adapter (Modular)

    Actor->>API: Sensitive Operation (Auth, SOS, Transition, Location Read, Export)
    API->>Service: Execute Domain Logic
    Service->>DB: Apply & Commit Business Mutation
    
    %% Audit Chaining Step
    Service->>AuditSvc: log_event(event_type, actor, resource, details)
    AuditSvc->>DB: Fetch Latest Event (get last event_hash & sequence_number)
    DB-->>AuditSvc: previous_hash (or GENESIS_HASH if seq #1)
    
    AuditSvc->>Hasher: calculate_event_hash(canonical_payload, previous_hash)
    Hasher->>Hasher: Sort keys, format ISO UTC timestamps, compute SHA-256
    Hasher-->>AuditSvc: event_hash
    
    AuditSvc->>DB: INSERT INTO audit_events (seq, type, actor_id, details, prev_hash, event_hash)
    DB-->>AuditSvc: Persisted
    AuditSvc-->>Service: Event recorded

    %% Verification & Trust Anchoring
    opt On-Demand Chain Verification (Admin/Auditor)
        Actor->>API: POST /api/v1/audit/verify
        API->>AuditSvc: verify_chain()
        AuditSvc->>DB: Query all AuditEvents ORDER BY sequence_number ASC
        DB-->>AuditSvc: Event Sequence
        AuditSvc->>Verifier: verify_chain(events)
        Verifier->>Verifier: Check genesis, forward pointers & payload digests
        Verifier-->>AuditSvc: ChainVerificationResult (CHAIN_VALID / CHAIN_BROKEN)
        AuditSvc-->>API: 200 OK (Verification Report)
    end

    opt Periodic Trust Checkpointing
        AuditSvc->>Anchor: anchor_checkpoint(sequence_number, event_hash)
        Anchor-->>AuditSvc: Checkpoint confirmation (Idempotent digest submission)
    end
```
