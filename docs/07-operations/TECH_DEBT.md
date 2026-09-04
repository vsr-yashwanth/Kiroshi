# Technical Debt Registry — KIROSHI

> Status: IMPLEMENTED (v0.1 Initial Tracking)

---

## Active Technical Debt Items

### TD-001: Mobile Flutter SDK Dependency on Developer Host
- **Problem**: The host workstation running Phase 0 lacked Flutter SDK in system PATH.
- **Impact**: Flutter widgets cannot be built or tested on this specific workstation without installing the Flutter SDK.
- **Why it exists**: Developer host environment constraint.
- **Proposed Solution**: Maintain strict syntax, clean architecture, and type contracts in `apps/mobile`; execute mobile builds in GitHub Actions CI where Flutter SDK is pre-configured.
- **Priority**: Medium.

### TD-002: Dual Dialect Database Abstraction (PostgreSQL vs SQLite)
- **Problem**: To enable friction-free development and tests without native PostgreSQL/Docker, SQLite is used locally.
- **Impact**: Dialect discrepancies (e.g. DateTime timezone handling and spatial types in later milestones).
- **Why it exists**: Prevents blocking local developers who do not have Docker running.
- **Proposed Solution**: In milestone v0.2.0 (Geospatial), enforce Docker PostGIS container for all local spatial integration tests.
- **Priority**: High (for v0.2).

### TD-003: Token Revocation / Blacklisting
- **Problem**: v0.1 issues stateless JWT tokens without a server-side revocation blacklist.
- **Impact**: Logout currently relies on client-side token discarding until token expiry.
- **Why it exists**: Minimal necessary complexity for v0.1 foundational auth.
- **Proposed Solution**: Introduce Redis-backed token denylist in future security hardening (v0.4/v1.0).
- **Priority**: Low.
