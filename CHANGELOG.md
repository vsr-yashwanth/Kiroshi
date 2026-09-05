# Changelog

All notable changes to the KIROSHI platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-09-05

### Added
- **Production Observability & Structured JSON Logging (`backend/app/core/logging.py`)**: Standardized JSON log formatter with automatic timestamping, module resolution, and credential redaction.
- **Request Tracing Middleware (`backend/app/main.py`)**: Injected `X-Request-ID` correlation headers and measured millisecond response latency headers (`X-Response-Time-MS`).
- **Readiness Probe (`GET /ready`)**: Dedicated probe for container orchestrators and load balancers verifying PostgreSQL connection pool health.
- **Database Connection Pooling**: Configured `pool_size=10`, `max_overflow=20`, `pool_timeout=30`, `pool_recycle=1800`, and `pool_pre_ping=True` in `backend/app/core/database.py`.
- **Comprehensive Benchmark Suite (`backend/tests/test_performance_benchmarks.py`)**: Measured and validated sub-millisecond latencies for Risk Engine (<0.04ms), Fall Detector (<0.05ms), and Audit Hasher (<0.02ms).
- **Security Hardening Test Suite (`backend/tests/test_security_hardening.py`)**: Automated verification of 401 unauthenticated rejections, RBAC role boundaries, and 422 malformed payload error sanitization.
- **Root Docker Compose Environment (`docker-compose.yml`)**: One-command reproducible local and production deployment orchestrating PostGIS 16 and FastAPI backend.
- **Documentation & Architecture Diagrams**: Published `PORTFOLIO_REVIEW.md`, `V1_RELEASE_REPORT.md`, updated `SYSTEM_FLOW.md`, and refreshed `README.md`.

### Hardened
- All 110 automated backend tests verified passing with 100% success across all historical milestones (v0.1 through v1.0).
- Frontend builds verified for React Authority Dashboard (`npm run build`) and Flutter Mobile client (`pubspec.yaml` bumped to `1.0.0+1`).

---

## [0.7.0] — 2026-09-05

### Added
- **Cryptographic Audit Hash Chaining Engine (`backend/app/engines/audit/`)**: Deterministic SHA-256 forward pointer chaining (`AuditEvent`) linking every security-sensitive event to the preceding record with canonical JSON serialization and normalized UTC timestamps.
- **Audit Verification & Tamper Detection (`AuditChainVerifier`)**: Automated verification engine detecting payload tampering, broken previous hashes, deleted records, and reordered logs, returning explicit verification reports (`CHAIN_VALID` / `CHAIN_BROKEN` at sequence `#N`).
- **Comprehensive Security Instrumentation**:
  - `auth_service`: Audits login attempts, successes, failures, and logouts with IP and user agent.
  - `tourist_service`: Audits profile read, profile update, and privacy consent status modifications.
  - `location_service`: Audits location history queries and active spatial snapshot exports.
  - `incident_service`: Audits SOS dispatches, authoritative state machine transitions, and responder assignments.
  - `cctv_service`: Audits scoped CCTV footage investigation queries.
- **Audit REST API Endpoints (`backend/app/api/v1/endpoints/audit.py`)**:
  - `GET /api/v1/audit/events`: Paginated, filterable event inspection for administrators and authorities.
  - `POST /api/v1/audit/verify`: On-demand cryptographic chain verification.
  - `POST /api/v1/audit/export`: Audited security export with immutable logging of the export action itself.
- **Modular Trust Anchoring Adapter (`TrustAnchor`)**: Interface and implementations (`LocalTrustAnchor`, `SimulatedExternalRegistryAnchor`) supporting isolated periodic checkpoint anchoring.
- **Database Schema Migration (`d74e9301f203_add_v07_audit_events_table.py`)**: Persistent `audit_events` table with unique sequence numbers, foreign key nullability on account deletion, and indexes.
- **Full Documentation Suite**: Created `DATA_CLASSIFICATION.md`, `AUDIT_ARCHITECTURE_DECISION.md`, `THREAT_MODEL.md`, `DISASTER_RECOVERY.md`, and updated `SECURITY.md`, `PRIVACY.md`, `SYSTEM_FLOW.md`.
- **Automated Verification Test Suite**: Added `test_audit_crypto.py`, `test_audit_tamper_detection.py`, `test_audit_api.py`, and `test_e2e_v07_audit_workflow.py` (102/102 backend tests passing across v0.1–v0.7).

### Architecture Decisions
- **Blockchain Dependency Rejected for Core Platform**: Evaluated across 4 options and rejected direct blockchain integration for v0.7 core to eliminate life-critical SOS latency bottlenecks, gas token overhead, external RPC availability risks, and permanent PII immutability hazards.
- **Privacy & GDPR Right to Erasure**: Enforced `ON DELETE SET NULL` on `actor_id` and zero PII payloads in audit fields, ensuring tourist deletion does not break cryptographic hash chain continuity.

---

## [0.6.0] — 2026-09-05

### Added
- **Computer Vision & Fall Detection Engine (`ml/models/fall_detector.py`)**: Modular, explainable fall detection algorithm evaluating posture aspect ratios ($w/h > 0.95$), torso angles ($< 45^\circ$), vertical kinematic descent velocity ($> 0.25/\text{s}$), and prolonged ground dwell times ($> 1000\text{ms}$).
- **Decoupled ML Interface & Versioning (`ml/interfaces.py`)**: Standardized `DetectionResult` contract tracking `model_name` (`kiroshi-fall-detector`), `model_version` (`0.6.0`), calibrated confidence scores, and natural language explanations.
- **Critical Safety Guardrail**: Strict enforcement that Computer Vision outputs `POSSIBLE_FALL` and NEVER automatically claims `CONFIRMED_EMERGENCY`.
- **CCTV Domain Models & Migration (`Camera`, `CCTVInvestigation`)**: PostGIS-backed camera inventory with spatial GIST index and `cctv_investigations` audit table (Alembic migration `c63e8290f102`).
- **PostGIS Proximity Search & Scoped Investigation (`CCTVService`)**: Spatial discovery of cameras within `search_radius_meters` via `ST_DWithin` / `ST_Distance` and time-bounded footage analysis ($\pm 5$ minutes).
- **CCTV API Endpoints (`backend/app/api/v1/endpoints/cctv.py`)**: RBAC-protected endpoints for camera registration, proximity search, and scoped incident investigation.
- **Risk Engine Integration (`backend/app/engines/risk/`)**: Optional incorporation of `POSSIBLE_FALL` signals into the transparent risk evaluator without coupling core safety to ML availability.
- **Authority Dashboard CCTV Console (`IncidentDetailModal.tsx`)**: One-click scoped CCTV investigation trigger displaying camera count, status, and explainable fall evidence directly within the incident operations modal.
- **Reproducible Evaluation & Benchmarks (`ml/evaluation/evaluate.py`)**: Measured benchmark calculating precision (100%), recall (100%), F1 score (1.0000), and mean inference latency (0.031ms).
- **Comprehensive Documentation**: Added `FALL_DETECTION.md`, `CCTV.md`, `ML.md`, and `DATASETS.md` in `docs/05-intelligence/`.
- **Automated Test Suite**: Added `test_fall_detection.py`, `test_cctv_api.py`, and `test_e2e_v06_cv_workflow.py` (90/90 backend tests passing).

### Security & Privacy
- Zero facial recognition, biometric indexing, or indiscriminate surveillance.
- CCTV investigations are strictly **Incident-Scoped**, **Location-Scoped**, **Time-Scoped**, and **Authorization-Scoped**.
- Tamper-evident audit logging for every investigation query and camera search.
- Full ML failure isolation: core backend, authentication, GPS, and emergency SOS dispatch remain 100% operational if ML times out, fails, or is disabled.

---

## [0.5.0] — 2026-09-05

### Added
- **Offline-First Synchronization Engine (`backend/app/services/sync_service.py`)**: Centralized synchronization service processing ordered batches of offline events (`POST /api/v1/sync/events`) with partial batch failure isolation.
- **Server-Side Idempotency (`SyncRecord`)**: Dedicated `sync_records` database table and Alembic migration `b52e7189c101` with unique `idempotency_key` constraint preventing duplicate incidents, duplicate state transitions, and side effects across network retries.
- **Persistent Mobile Event Queue (`OfflineEventQueue`)**: Thread-safe FIFO storage queue backed by `SharedPreferences` that survives mobile application kills, crashes, and device reboots.
- **Critical Honesty Rule for Offline SOS**: Absolute requirement ensuring the mobile UI never claims "Emergency sent" when offline. Displays explicit "Emergency saved on device. It has NOT reached authorities yet" until authoritative server acknowledgement is received.
- **Active Backend Connectivity Awareness (`ConnectivityService`)**: Active health probing of backend reachability (`/api/v1/health`) rather than relying on superficial local Wi-Fi interface flags.
- **Offline State Machine (`SyncManager`)**: Unambiguous 5-state transitions (`ONLINE`, `OFFLINE`, `SYNCING`, `SYNCED`, `SYNC_ERROR`) with single-worker mutex locking and bounded exponential backoff ($2\text{s} \rightarrow 30\text{s}$).
- **Offline Trip Caching (`OfflineCacheService`)**: Local caching of active trip, itineraries, emergency contacts, and single last-known GPS fix with graceful offline degradation in `TripState`.
- **Global Connectivity & Honest SOS Banner (`ConnectivityBanner`)**: Real-time persistent visual indicator communicating current synchronization state and explicit offline SOS alerts across all application screens.
- **Comprehensive Test Coverage**: Added `test_sync_api.py` and `test_e2e_v05_offline_sync_workflow.py` validating single/batch sync, duplicate suppression, late-arriving timestamps, trip conflict resolution, and end-to-end offline lifecycle (84/84 passing).
- **Architecture Documentation & Decisions**: Added `docs/04-mobile/OFFLINE_MODE.md` and `docs/08-decisions/ADR-005-offline-sync.md`.

### Security
- Bounded local queue storage (1,000 items) preventing runaway disk growth while strictly preserving all life-critical SOS beacons.
- Storage data minimization: zero caching of user passwords, raw auth tokens stored exclusively in secure platform storage (`flutter_secure_storage`), and suppression of excessive historic breadcrumbs.
- Server-authoritative conflict resolution enforcing RBAC and rejecting unauthorized state transitions from stale offline events.

---

## [0.4.0] — 2026-09-04


### Added
- **Incident Domain (`backend/app/domain/models/incident*.py`)**: Dedicated, independent domain models for `Incident`, `IncidentEvent`, and `IncidentAssignment` with Alembic migration `a41d9230e71b`.
- **Authoritative Incident State Machine (`IncidentStateMachine`)**: Strict 9-state transition machine (`DETECTED`, `VERIFYING`, `VERIFIED`, `ESCALATED`, `ASSIGNED`, `RESPONDING`, `RESOLVED`, `CLOSED`, `DISMISSED`) rejecting invalid state skips and mutations on terminal states.
- **Role-Aware State Authorization**: Integrated RBAC into state transitions: Tourists cannot resolve or close; Responders can only inspect and transition incidents assigned to them; Authorities can triage, verify, escalate, assign, and close.
- **Life-Critical Emergency SOS Beacon (`POST /api/v1/incidents/sos`)**: 100% decoupled from AI, ML, CCTV, and external gateways. Captures fresh GPS or gracefully falls back to `UNKNOWN` without blocking incident creation.
- **SOS Idempotency Protection**: Client-generated `idempotency_key` prevents duplicate incident creation from network retries and double taps.
- **Append-Only Incident Timeline**: Chronological, immutable `IncidentEvent` audit trail tracking every transition, actor, role, timestamp, and operational reason.
- **Pluggable Notification Infrastructure**: `NotificationService` with `InAppNotificationProvider`, delivery retries, idempotency, and guaranteed failure isolation (notification failure never rolls back incident creation).
- **Real-Time WebSocket Incident Pipeline**: Broadcaster emitting `INCIDENT_CREATED`, `INCIDENT_STATUS_CHANGED`, and `INCIDENT_ASSIGNED` over `/api/v1/ws/authority`.
- **Authority Dashboard Operations Console**: React 19 incident console (`IncidentsPage.tsx` and `IncidentDetailModal.tsx`) featuring real-time queue metrics, severity and status filters, responder assignment modal, and chronological event timeline.
- **Mobile Tourist SOS Integration**: Deliberate confirmation bottom sheet (`sos_confirmation_sheet.dart`) and emergency SOS entry points in live tracking and trip list screens.
- **Comprehensive Automated Test Suite**: 16 new automated tests covering state machine transitions, invalid terminal rejection, SOS failure modes, notifications, API access control, and complete end-to-end emergency lifecycle (79/79 total passing).

### Security
- Anti-IDOR enforcement ensuring field responders can only access and update incidents assigned to them.
- Terminal state immutability preventing `CLOSED` or `DISMISSED` incidents from being resurrected or modified.
- Strict isolation guaranteeing that optional service outages (Risk Engine, AI, notification networks) never compromise SOS distress persistence.

---

## [0.3.0] — 2026-09-04

### Added
- **Intelligent Risk Engine Domain (`backend/app/engines/risk/`)**: Created modular, deterministic rule engine (`v0.3-rule-engine`) evaluating composite risk scores ($[0.0, 1.0]$) from real-time spatial and behavioral telemetry.
- **Route Deviation Evaluator**: Point-to-segment geodesic cross-track distance mathematics projecting tourist positions against itinerary polyline sequences with configurable tolerance tiers.
- **Hazard & Regulatory Zone Evaluators**: Evaluates containment within PostGIS `HIGH_RISK` natural hazards and `RESTRICTED` legal zones.
- **Inactivity Evaluator**: Multi-ping trajectory analyzer detecting prolonged stationary immobility ($\le 15\text{m}$) over 30-minute and 60-minute thresholds.
- **Movement Speed Evaluator**: Flags excessive velocity exceeding transport modality tolerances.
- **Natural Language Risk Explainer**: Generates operational summaries articulating contributing hazards for human verification.
- **Multi-Factor Data Confidence Metric**: Calculates observational confidence ($[0.10, 1.00]$) based on GPS accuracy, location freshness, trajectory depth, and route context.
- **Risk Persistence Model (`RiskAssessment`)**: Added SQLAlchemy model and Alembic migration (`f2ae5b201aa7`) with composite indexes on `(tourist_id, created_at DESC)` and `(trip_id, created_at DESC)`.
- **Risk REST Endpoints**: Added `GET /api/v1/risk/current/{tourist_id}`, `GET /api/v1/risk/history/{trip_id}`, and `GET /api/v1/risk/active` with strict IDOR protections.
- **Real-Time Risk Broadcasting**: Selective WebSocket event propagation (`RISK_UPDATE`) triggered upon meaningful state transitions, delivered to subscribed dispatch consoles.
- **Authority Dashboard Risk Inspector**: Interactive modal drawer (`RiskInspectorModal.tsx`) with real-time risk gauges, contributing signal breakdowns, confidence scores, and historical timeline.
- **Automated Test Suite**: Added 30 new tests covering scenarios A through H, threshold boundaries, 100-run determinism, API RBAC, and complete v0.3 end-to-end integration workflow (63/63 passing).
- **Technical Documentation**: Added `RISK_ENGINE.md` and `ML.md` to `docs/05-intelligence/`, detailing scoring formulas, thresholds, confidence, and roadmap.

### Security
- Enforced strict IDOR protection preventing tourists from querying other tourists' risk assessments or history.
- Restricted system-wide active risk snapshot endpoints and WebSocket risk subscriptions strictly to `AUTHORITY` and `ADMIN` roles.

---

## [0.2.0] — 2026-09-04

### Added
- **PostGIS Spatial Persistence**: Integrated `GeoAlchemy2` and PostGIS 3.4 Point and Polygon types with SRID 4326 and spatial GIST indexes.
- **Location Ingestion API**: Implemented `POST /api/v1/location` with server-side coordinate range checking, clock skew boundaries, accuracy limits, and active trip ownership verification.
- **Trip Trajectory API**: Added `GET /api/v1/location/history/{trip_id}` and `GET /api/v1/location/active` for route history and live positions.
- **GeoZone Management**: Added `GET /api/v1/zones`, `POST /api/v1/zones`, `DELETE /api/v1/zones/{id}`, and `GET /api/v1/zones/events` for polygon safety perimeters (`SAFE`, `RESTRICTED`, `HIGH_RISK`, `CUSTOM`).
- **Geofence State Transition Machine**: Implemented edge-triggered spatial containment evaluation using PostGIS `ST_Covers`, generating discrete `ENTER` and `EXIT` events with zero duplicate spamming.
- **Authenticated WebSockets**: Created full-duplex `/api/v1/ws/authority` endpoint supporting token handshake authentication, role-based access control, initial snapshot hydration, heartbeat keepalives, and fault-isolated fanout.
- **Authority Dashboard Live Map**: Added interactive SVG/GIS map component (`LiveMonitoringMap.tsx`), real-time WebSocket hook (`useLiveStream.ts`), and command center page (`LiveMonitoringPage.tsx`) with tourist markers, breadcrumb trails, geozone overlays, and live alert feed.
- **Mobile Location Tracking**: Added Flutter GPS tracking service (`LocationTrackingService`), state machine (`LocationState`), permissions management, battery-efficient 10m distance filtering, and real-time telemetry screen (`LiveTrackingScreen`).
- **Automated Testing Suite**: Added 17 new tests covering location ingestion validation, PostGIS spatial queries, geofence state transitions, WebSocket RBAC, and complete v0.2 end-to-end workflow (33/33 total passing).
- **Documentation**: Added `REALTIME.md`, `LOCATION_TRACKING.md`, `GEO_FENCING.md`, `ADR-003-websocket-realtime.md`, and `ADR-004-postgis-spatial-engine.md`.

### Security
- Derived `tourist_id` strictly from verified JWT claims to prevent IDOR and cross-user location spoofing.
- Enforced WebSocket RBAC restricting live telemetry streams exclusively to `AUTHORITY` and `ADMIN` roles.
- Sanitized real-time telemetry frames to prevent leaking unnecessary PII over live streams.

---

## [0.1.0] — 2026-09-04

### Added
- **Repository Architecture**: Initialized repository structure following domain-driven modular monolith guidelines.
- **Environment Isolation**: Configured Python `.venv` management and project-local Node dependency governance.
- **Backend Architecture**: Layered FastAPI backend with clean separation of concerns (`api/`, `core/`, `domain/`, `services/`, `repositories/`).
- **Database Schema**: Established SQLAlchemy 2.0 models and Alembic migrations for `User`, `TouristProfile`, `Trip`, and `Itinerary`.
- **Authentication**: JWT token issuance, verification, and bcrypt password hashing.
- **Server-Side Authorization**: Role-based access control supporting `TOURIST`, `AUTHORITY`, `RESPONDER`, and `ADMIN`.
- **Trip Lifecycle API**: Endpoints for trip creation, itinerary waypoint specification, trip start, and trip stop with status tracking.
- **Authority Dashboard**: React 19 + TypeScript + Vite web application for authorities to view tourists, active trips, and system health.
- **Flutter Mobile Foundation**: Mobile architecture specification with Domain, Application, Presentation, and Infrastructure layers.
- **Automated Testing Suite**: Automated pytest suite covering authentication, ownership validation, authorization, and trip state machines.
- **Documentation**: Comprehensive technical documentation suite across overview, architecture, backend, mobile, security, and operations.

### Security
- Server-side authorization preventing IDOR (Insecure Direct Object Reference) on tourist profile and trip resources.
- Strict password hashing via bcrypt with configurable salt rounds.
- Environment-based secret configuration via `.env` (gitignored).

### Known Limitations
- Real-time WebSockets and live GPS streaming are deferred to v0.2.0.
- Machine learning risk engine is deferred to v0.3.0.
- Flutter SDK is not installed on the current host machine; mobile test execution is deferred to a CI environment or an SDK-equipped workstation.
