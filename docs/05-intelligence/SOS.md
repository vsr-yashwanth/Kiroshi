# Emergency SOS Architecture (v0.4)

## 1. Overview & Core Reliability Directive

The Emergency SOS system represents the primary panic and distress beacon mechanism for travelers using the KIROSHI platform.

### Critical SOS Reliability Rule
```
Authenticated Tourist
    ↓
SOS REST API (/api/v1/incidents/sos)
    ↓
Location Resolution (Fresh / DB Stale / UNKNOWN)
    ↓
Incident Database Persistence (Status: DETECTED, Severity: CRITICAL)
    ↓
Real-Time Authority WebSocket Broadcast & In-App Notifications
```

**MANDATORY ARCHITECTURAL DECOUPLING:**
If the following optional services or components fail or are unavailable:
- AI / Machine Learning services
- Risk Assessment Engine
- CCTV / Video feeds
- External SMS / Push / Email gateways
- Blockchain / Cryptographic audit networks

**THE SOS WORKFLOW MUST STILL SUCCEED AND PERSIST THE INCIDENT.**
Emergency distress beacons are life-critical paths that must execute independently of predictive intelligence or external networks.

---

## 2. Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Tourist as Tourist Mobile App
    participant API as FastAPI /api/v1/incidents/sos
    participant GPS as Location Subsystem
    participant DB as PostgreSQL (PostGIS)
    participant WS as WebSocket ConnectionManager
    participant Notif as InAppNotificationProvider
    actor Authority as Authority Dashboard

    Tourist->>Tourist: Press SOS & Deliberate Confirmation Sheet
    Tourist->>GPS: Request Current Device Coordinates (4s timeout)
    alt GPS Available
        GPS-->>Tourist: Latitude, Longitude, Accuracy
    else GPS Timed Out / Denied
        GPS-->>Tourist: null (Fallback)
    end
    Tourist->>API: POST /api/v1/incidents/sos (idempotency_key, coords, notes)
    API->>DB: Check Idempotency Key
    alt Duplicate Request Found
        DB-->>API: Existing Incident Record
        API-->>Tourist: 200 OK (Return Existing Incident)
    else New Request
        API->>DB: Resolve Location (Input Coords -> Last DB Loc -> UNKNOWN)
        API->>DB: Insert Incident (DETECTED, CRITICAL, SOS)
        API->>DB: Insert IncidentEvent (INCIDENT_CREATED)
        API->>DB: Commit Transaction
        par Asynchronous Notifications & Broadcast
            API->>WS: Broadcast INCIDENT_CREATED to Authorities
            WS-->>Authority: Display in Real-Time Queue
        and
            API->>Notif: Deliver In-App Notifications
        end
        API-->>Tourist: 201 Created (Incident Object)
    end
```

---

## 3. Location Capture & Resilience

The SOS workflow handles location gracefully across all edge scenarios:

| Sensor State | Freshness Classification | Database Representation | Behavior |
| :--- | :--- | :--- | :--- |
| Fresh GPS Fix (within 4s) | `LIVE` | Point geometry & lat/lng | Immediate geo-containment matching |
| Stale GPS Fix (&lt; 5 mins) | `RECENT` | Last known Point geometry | Flagged as recent telemetry |
| Stale GPS Fix (&gt; 5 mins) | `STALE` | Last known Point geometry | Flagged as stale telemetry |
| GPS Disabled / Denied / Underground | `UNKNOWN` | `NULL` geometry & lat/lng | **Incident created successfully** without coordinates |

**Under no circumstances will a GPS timeout or missing sensor reading block emergency incident persistence.**

---

## 4. Duplicate Suppression (Idempotency)

Under stressful emergency situations or poor cellular connectivity, tourists may tap the SOS button repeatedly or network clients may retry unacknowledged requests.

1. **Client-Generated Idempotency Key**:
   The tourist mobile client generates an idempotency key (format: `sos-<timestamp>-<rand>`) before initial dispatch.
2. **Server-Side Deduplication**:
   The server checks the `incidents.idempotency_key` unique constraint:
   - If an incident with the given key already exists in the database, the existing incident record is returned immediately with HTTP 200.
   - No duplicate incident row or redundant notification cascade is generated.
