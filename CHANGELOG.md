# Changelog

All notable changes to the KIROSHI platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
