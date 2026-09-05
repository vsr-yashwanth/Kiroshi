# ADR-005 — Offline Synchronization, Persistence Strategy, and Idempotency

## Status
Accepted

## Context
In remote wilderness, mountain routes, maritime coasts, and international roaming scenarios, cellular connectivity is frequently unavailable. Safety-critical distress signaling (SOS), trajectory breadcrumbs, and trip state mutations must function reliably when disconnected. Furthermore, intermittent reconnection creates risk of duplicate submissions, out-of-order execution, and inconsistent server state.

## Options Considered
1. **Full Embedded Relational Database on Mobile (SQLite / Drift)**: Heavy native compilation footprint, schema synchronization maintenance, and complex mobile-to-server schema alignment.
2. **Key-Value Serialized Queue on SharedPreferences & Secure Storage**: Lightweight, zero-native compilation friction, persistent across process restarts, and bounded capacity.
3. **Optimistic Client-Authoritative Sync**: Mobile state directly overwrites server state upon reconnection.
4. **Authoritative Server Sync with Explicit Idempotency Keys**: Server remains single source of truth; client provides unique nonces for deduplication and receives explicit conflict/duplicate acknowledgements.

## Decision
1. Utilize **Persistent JSON Queue on `SharedPreferences`** for event queuing and local caching, combined with `flutter_secure_storage` for credentials.
2. Implement **Authoritative Server Idempotency** backed by a dedicated `sync_records` table and unique `idempotency_key` constraints.
3. Expose a unified batch endpoint **`POST /api/v1/sync/events`** with partial batch failure isolation.
4. Enforce the **Critical Honesty Rule**: mobile UI displays "Saved locally, not yet sent" until authoritative server ACK is received.

## Rationale
- Zero additional heavy native C-libraries or third-party database dependencies introduced on mobile.
- Completely prevents duplicate incidents, state transitions, and side-effects even across aggressive retries and network drops.
- Partial batch tolerance prevents single malformed events from blocking life-critical emergency beacons.
- Server maintains absolute authority over lifecycle state machines.

## Consequences
- Requires mobile client to generate collision-resistant idempotency keys (`{prefix}-{timestamp}-{rand}`).
- Server must audit processed keys in `sync_records` to provide idempotent duplicate responses.
- Queue capacity must be bounded (capped at 1,000 items) to prevent runaway disk usage.

## Rejected Alternatives
- SQLite/Drift rejected for mobile as premature complexity when bounded queue storage on SharedPreferences satisfies all functional and resilience requirements.
- Client-authoritative sync rejected because safety-critical state transitions (e.g. incident resolution) must be strictly governed by server RBAC.
