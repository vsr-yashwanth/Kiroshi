# Changelog

All notable changes to the KIROSHI platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
