# KIROSHI System Architecture & Subsystem Flows (v1.0)

> Status: IMPLEMENTED (v1.0 Production Release)

---

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph Clients ["Client Applications"]
        Mobile["Flutter Mobile App (Tourist)"]
        Dashboard["React TypeScript Console (Authority & Responders)"]
    end

    subgraph Gateway ["API Gateway & Middleware Layer"]
        FastAPI["FastAPI Application Gateway"]
        AuthMiddleware["JWT Authentication & RBAC Filter"]
        Observability["X-Request-ID & Timing Observability"]
    end

    subgraph CoreServices ["Core Domain & Intelligence Services"]
        AuthService["Auth & Identity Service"]
        TouristService["Tourist Profile Service"]
        TripService["Trip & Itinerary Manager"]
        LocationService["Location Ingestion & PostGIS Spatial Filter"]
        RiskEngine["Deterministic Rule-Based Risk Engine"]
        IncidentService["Authoritative Incident State Machine"]
        SyncService["Offline-First Sync & Idempotency Manager"]
        CVService["Fall Detector & Scoped CCTV Analyzer"]
        AuditService["Cryptographic Audit Chaining Engine"]
    end

    subgraph Persistence ["Persistence & Storage Layer"]
        PostgreSQL[("PostgreSQL 16 + PostGIS 3.4")]
        WAL["Write-Ahead Logging / Encrypted Backups"]
        TrustAnchor["Trust Anchor Adapter (SHA-256 Checkpoints)"]
    end

    Mobile -->|REST API & WebSocket| FastAPI
    Dashboard -->|REST API & WebSocket| FastAPI
    FastAPI --> AuthMiddleware --> Observability
    Observability --> CoreServices
    CoreServices --> PostgreSQL
    AuditService --> TrustAnchor
    PostgreSQL --> WAL
```

---

## 2. Location Tracking & Geospatial Pipeline Flow

```mermaid
sequenceDiagram
    autonumber
    actor Tourist as Tourist Mobile Device
    participant API as Location Endpoint (/api/v1/location)
    participant PostGIS as PostgreSQL / PostGIS Engine
    participant Risk as Risk Assessment Engine
    participant WS as WebSocket ConnectionManager
    actor Authority as Authority Monitoring Dashboard

    Tourist->>API: POST Location (lat, lon, speed, accuracy, trip_id)
    API->>PostGIS: ST_SetSRID(ST_MakePoint(lon, lat), 4326)
    API->>PostGIS: ST_Contains(geozones.polygon, location_point)
    PostGIS-->>API: Active Safety & Hazard Zones
    API->>Risk: Calculate Risk Score (Geofence + Velocity + Itinerary)
    Risk-->>API: Risk Evaluation Result (Score, Level, Explanation)
    API->>WS: Broadcast sanitized location & risk payload
    WS-->>Authority: Live Map Telemetry Frame
    API-->>Tourist: 201 Created (Location Point + Zone Warnings)
```

---

## 3. Explainable Risk Scoring Engine Pipeline Flow

```mermaid
graph LR
    subgraph Inputs ["Real-Time Telemetry Inputs"]
        GPS["GPS Position & Accuracy"]
        Waypoints["Itinerary Route Segments"]
        Zones["Active High-Risk / Restricted Geozones"]
        History["Movement Velocity & Inactivity History"]
        CV["Computer Vision (Possible Fall Signals)"]
    end

    subgraph SignalEvaluators ["Signal Evaluators (RiskConfig Policy)"]
        DevEval["Route Deviation Evaluator (0.35 weight)"]
        ZoneEval["Geozone Risk Evaluator (0.45 weight)"]
        InactEval["Inactivity Evaluator (0.25 weight)"]
        SpeedEval["Speed Dynamics Evaluator (0.15 weight)"]
        CVEval["CV Fall Signal Evaluator (0.30 weight)"]
    end

    subgraph DecisionEngine ["Deterministic Aggregator"]
        Weighting["Weighted Contribution Normalizer"]
        Thresholds["Threshold Classifier (SAFE / LOW / MED / HIGH / CRITICAL)"]
        Explainer["Natural Language Explanation Generator"]
    end

    Inputs --> SignalEvaluators
    SignalEvaluators --> Weighting --> Thresholds --> Explainer
```

---

## 4. Emergency Response & Incident Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> DETECTED: SOS Triggered / Beacon Received
    DETECTED --> VERIFYING: Authority Begins Triage
    DETECTED --> DISMISSED: Authority Marks False Alarm
    VERIFYING --> VERIFIED: Distress Confirmed
    VERIFYING --> DISMISSED: De-escalated / False Alarm
    VERIFIED --> ESCALATED: Threat Level Elevated
    VERIFIED --> ASSIGNED: Field Responder Dispatched
    ESCALATED --> ASSIGNED: Emergency Units Dispatched
    ASSIGNED --> RESPONDING: Responder Acknowledges & En Route
    RESPONDING --> RESOLVED: Tourist Safe / Incident Handled
    RESOLVED --> CLOSED: Authority Completes After-Action Report
    CLOSED --> [*]
    DISMISSED --> [*]
```

---

## 5. Offline-First Synchronization & Event Queue Flow

```mermaid
sequenceDiagram
    autonumber
    actor Tourist as Tourist Mobile App (Offline)
    participant Queue as Persistent FIFO Event Queue
    participant Sync as SyncManager Worker
    participant API as Sync Endpoint (/api/v1/sync/events)
    participant DB as PostgreSQL Database

    Tourist->>Queue: Enqueue Location / SOS / Profile Event
    Queue-->>Tourist: Stored locally in encrypted SharedPreferences
    Note over Tourist: Banner: "Emergency saved on device. NOT sent yet"

    Sync->>Sync: Connectivity Probe (/api/v1/health -> Reachable)
    Sync->>Queue: Drain Ordered Batch (Idempotency Keys)
    Sync->>API: POST /api/v1/sync/events (Batch)
    API->>DB: Check idempotency_key uniqueness in sync_records
    DB-->>API: Idempotent commit & process domain mutation
    API-->>Sync: 200 OK (Batch Processing Result)
    Sync->>Queue: Delete processed events from local queue
    Note over Tourist: Banner: "Synchronized with authorities"
```

---

## 6. Cryptographic Audit Chaining & Trust Verification Flow

```mermaid
sequenceDiagram
    autonumber
    actor Actor as User / System Operation
    participant Service as Business Domain Service
    participant AuditSvc as AuditService
    participant Hasher as AuditHasher (SHA-256)
    participant DB as audit_events Table
    participant Verifier as AuditChainVerifier

    Actor->>Service: Execute Sensitive Operation (Auth, SOS, Transition, Export)
    Service->>DB: Commit Business Record
    Service->>AuditSvc: log_event(type, actor, resource, details)
    AuditSvc->>DB: Fetch Latest Sequence # and Event Hash
    DB-->>AuditSvc: previous_hash (or GENESIS_HASH if #1)
    AuditSvc->>Hasher: calculate_event_hash(canonical_payload, previous_hash)
    Hasher->>Hasher: Canonical JSON (sorted keys, ISO UTC timestamps) -> SHA-256
    Hasher-->>AuditSvc: event_hash
    AuditSvc->>DB: INSERT INTO audit_events
    
    opt Verification Check
        Actor->>Verifier: POST /api/v1/audit/verify
        Verifier->>DB: Query all events ORDER BY sequence_number ASC
        Verifier->>Verifier: Validate genesis root, forward pointers & payload digests
        Verifier-->>Actor: ChainVerificationResult (CHAIN_VALID / CHAIN_BROKEN at #N)
    end
```
