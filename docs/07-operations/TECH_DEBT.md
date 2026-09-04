# Technical Debt Registry — KIROSHI

> Status: UPDATED (v0.2 Tracking)

---

## Active Technical Debt Items

### TD-001: Mobile Flutter SDK Dependency on Developer Host
- **Problem**: The host workstation running development lacks Flutter SDK in system PATH.
- **Impact**: Flutter widgets cannot be built or tested on this specific workstation without installing the Flutter SDK.
- **Why it exists**: Developer host environment constraint.
- **Mitigation**: Maintain strict syntax, clean architecture, and type contracts in `apps/mobile`; execute mobile builds in GitHub Actions CI where Flutter SDK is pre-configured.
- **Priority**: Medium.

### TD-002: Dual Dialect Database Abstraction (PostgreSQL vs SQLite)
- **Status**: PARTIALLY RESOLVED (v0.2).
- **Resolution**: Implemented custom SQLite user-defined spatial functions with Shapely bindings (`ST_Covers`, `ST_SetSRID`, `AsEWKB`, `GeomFromEWKT`) allowing 100% of spatial tests to pass locally, while CI tests run against PostgreSQL 16 + PostGIS 3.4 in Docker container.
- **Remaining Debt**: Native SQLite SpatiaLite dynamic library is not bundled for production SQLite use (PostgreSQL + PostGIS is required in production).
- **Priority**: Low.

### TD-003: Token Revocation / Blacklisting
- **Problem**: Stateless JWT tokens without a server-side revocation blacklist.
- **Impact**: Logout currently relies on client-side token discarding until token expiry.
- **Why it exists**: Minimal necessary complexity for foundational auth.
- **Proposed Solution**: Introduce Redis-backed token denylist in future security hardening (v0.4/v1.0).
- **Priority**: Low.

### TD-004: In-Memory WebSocket Connection Registry
- **Problem**: `WebSocketManager` tracks active connections in-process via Python `Set[WebSocket]`.
- **Impact**: Broadcasts only reach clients connected to the same FastAPI worker process.
- **Why it exists**: Appropriate for single-instance modular monolith in v0.2.
- **Proposed Solution**: Introduce Redis Pub/Sub channel backplane when scaling to multi-replica deployment in v0.4+.
- **Priority**: Medium (Post-v0.2).

### TD-005: Mobile Offline Telemetry Queue
- **Problem**: When network connectivity drops, telemetry points are logged to error state without persistent on-device SQLite queuing.
- **Impact**: Transient offline points are not retransmitted upon reconnection.
- **Why it exists**: Scoped explicitly to milestone v0.5 (Offline-First Synchronization).
- **Proposed Solution**: Implement drift-tolerant local SQLite sync engine in v0.5.
- **Priority**: Scheduled for v0.5.
