# ADR-003: WebSocket Architecture for Real-Time Geospatial Broadcast

## Status
ACCEPTED

## Context
In KIROSHI v0.2, authorities need immediate, low-latency visibility into tourist positions and geofence crossings. Traditional HTTP polling (`GET /api/v1/location/active` every N seconds) introduces latency, burns unnecessary server CPU, and creates bursty database load. Server-Sent Events (SSE) offer unidirectionality but lack standard bidirectional keepalive/heartbeat negotiation across complex proxies.

## Decision
We implemented a centralized, authenticated WebSocket endpoint (`/api/v1/ws/authority`) managed by an asynchronous `WebSocketManager` service.

Key architectural characteristics:
1. **Authentication via Query Parameter**: Because browser `WebSocket` APIs cannot attach custom `Authorization: Bearer` headers during the HTTP upgrade handshake, the JWT token is passed as `?token=<jwt>` and verified immediately prior to connection acceptance.
2. **Strict RBAC**: Only authenticated users with `AUTHORITY` or `ADMIN` roles are permitted. Unauthorized attempts are rejected with standard WebSocket close code `1008 Policy Violation`.
3. **Isolated Broadcasts**: The `WebSocketManager` broadcasts concurrently across registered client websockets, catching individual socket disconnections or buffer overflows without terminating broadcasts to other connected authorities.
4. **Initial State Hydration**: Upon connection, clients immediately receive an initial `snapshot` frame containing all currently active tourists and their latest known telemetry. Subsequent updates arrive incrementally as `location_update` or `zone_event` frames.
5. **Bidirectional Heartbeats**: Clients periodically transmit `{"type": "ping"}` to maintain connection liveness through NATs, receiving `{"type": "pong"}` replies.

## Consequences
- **Positive**: Sub-second latency for live marker animation and immediate geofence danger alerts. Reduced HTTP overhead and database query volume compared to continuous client polling.
- **Negative**: Long-lived TCP connections require stateful connection tracking in memory. For multi-node scale-out in future milestones (v0.4+), an external pub/sub layer (such as Redis Pub/Sub) will be needed to synchronize broadcasts across backend replicas.
