# Real-Time & WebSocket Architecture — KIROSHI v0.2

> Status: IMPLEMENTED (v0.2) | Endpoint: `/api/v1/ws/authority`

---

## 1. Overview

KIROSHI v0.2 implements an asynchronous real-time event pipeline to provide tourism authorities with sub-second situational awareness. Location updates ingested via `POST /api/v1/location` are immediately validated, persisted in PostGIS, processed against geofencing rules, and broadcast over authenticated WebSockets to connected authority command consoles.

```
Tourist Mobile (GPS)
       │  POST /api/v1/location (Bearer JWT)
       ▼
FastAPI Location Service
       │
       ├─► PostgreSQL 16 / PostGIS (Persist LocationEvent)
       │
       ├─► PostGIS ST_Covers Spatial Query
       │      │
       │      ▼
       │   Evaluate Zone State Transitions (ENTER / EXIT)
       │
       └─► WebSocket Broadcast Manager
              │
              ├─► Authority Dashboard 1 (Live GIS Map)
              ├─► Authority Dashboard 2 (Incident Command)
              └─► Broadcast Fan-out (Isolated try-catch per connection)
```

---

## 2. WebSocket Authentication & RBAC

### 2.1 Connection Protocol
WebSockets cannot reliably transmit custom HTTP headers in standard browser JavaScript APIs. Therefore, authentication occurs via URL query parameter during the initial HTTP Upgrade handshake:

```
ws://<host>:<port>/api/v1/ws/authority?token=<AUTHORITY_JWT_ACCESS_TOKEN>
```

### 2.2 Security Enforcement
1. **Token Verification**: The server extracts `token`, decodes the signature using `SECRET_KEY`, and checks expiration.
2. **Role Verification**: The user's role must be `AUTHORITY` or `ADMIN`.
3. **Rejection**: If the token is missing, invalid, expired, or belongs to a user with role `TOURIST` or `RESPONDER`, the handshake is terminated with standard WebSocket close code:
   - `1008 Policy Violation`
   - Rejection message: `{"error": "Unauthorized authority access"}`

---

## 3. Protocol Message Envelopes

All WebSocket messages exchanged adhere to standard JSON envelopes:

### 3.1 Server-to-Client Messages

#### 1. Initial State Snapshot (`type: "snapshot"`)
Sent immediately upon successful connection establishment to hydrate the dashboard with currently active tourists and their latest known positions:

```json
{
  "type": "snapshot",
  "active_count": 2,
  "data": [
    {
      "tourist_id": "c1f72922-83b4-4b51-b844-3bc7bfba5555",
      "tourist_name": "Jane Doe",
      "trip_id": "7b8971f4-3450-424a-9b16-562aef768222",
      "trip_title": "Himachal Ridge Trek",
      "latitude": 32.2432,
      "longitude": 77.1892,
      "accuracy": 8.5,
      "speed": 1.2,
      "recorded_at": "2026-09-04T10:15:30Z",
      "freshness": "LIVE"
    }
  ],
  "timestamp": "2026-09-04T10:15:32Z"
}
```

#### 2. Live Location Update (`type: "location_update"`)
Broadcast whenever an active tourist transmits a new GPS position:

```json
{
  "type": "location_update",
  "data": {
    "tourist_id": "c1f72922-83b4-4b51-b844-3bc7bfba5555",
    "trip_id": "7b8971f4-3450-424a-9b16-562aef768222",
    "latitude": 32.2435,
    "longitude": 77.1895,
    "accuracy": 6.2,
    "speed": 1.4,
    "heading": 42.0,
    "recorded_at": "2026-09-04T10:15:45Z",
    "freshness": "LIVE"
  },
  "timestamp": "2026-09-04T10:15:46Z"
}
```

#### 3. Geofence Boundary Alert (`type: "zone_event"`)
Broadcast immediately when a tourist crosses a geofence boundary:

```json
{
  "type": "zone_event",
  "data": {
    "event_type": "ENTER",
    "tourist_id": "c1f72922-83b4-4b51-b844-3bc7bfba5555",
    "zone_id": "8e3b2e91-c529-4d6b-9c71-337c76a59111",
    "zone_name": "Solang Avalanche Zone",
    "zone_type": "HIGH_RISK",
    "latitude": 32.2450,
    "longitude": 77.1910,
    "occurred_at": "2026-09-04T10:16:02Z"
  },
  "timestamp": "2026-09-04T10:16:02Z"
}
```

#### 4. Heartbeat Keepalive (`type: "ping"` / `type: "pong"`)
The connection manager supports bidirectional keepalives. When the client sends `{"type": "ping"}`, the server immediately responds with:

```json
{
  "type": "pong",
  "timestamp": "2026-09-04T10:16:30Z"
}
```

---

## 4. Connection Resilience & Fault Isolation

1. **Broadcast Isolation**: The `WebSocketManager` wraps each client dispatch in an isolated exception block. If a client disconnects abruptly or has a full socket buffer, the broken socket is purged from the registry without interrupting broadcasts to other clients.
2. **Automatic Reconnection**: The frontend client (`useLiveStream.ts`) implements an exponential backoff reconnection strategy (starting at 2s up to 30s) upon unexpected disconnection.
3. **Heartbeat Monitoring**: The dashboard client dispatches periodic ping frames every 30 seconds to prevent NAT and proxy timeouts.
