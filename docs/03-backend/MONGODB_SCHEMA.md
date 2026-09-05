# KIROSHI — MongoDB Database Specification & Schema Architecture

> **Connection String:** `mongodb://localhost:27017/Kiroshi`  
> **Database Scope:** Isolated strictly to database `Kiroshi` on local instance  
> **Schema Definition File:** [`docs/03-backend/mongodb_schemas.json`](file:///d:/Yashwanth/Programming/Kiroshi/docs/03-backend/mongodb_schemas.json)  
> **Migration & Setup Script:** [`scripts/migrate_to_mongodb.py`](file:///d:/Yashwanth/Programming/Kiroshi/scripts/migrate_to_mongodb.py)

---

## 1. Architectural Role & Dual-Database Strategy

In accordance with KIROSHI Engineering Governance ([ADR-002](file:///d:/Yashwanth/Programming/Kiroshi/docs/08-decisions/ADR-002-database-strategy.md), [ADR-004](file:///d:/Yashwanth/Programming/Kiroshi/docs/08-decisions/ADR-004-postgis-spatial-engine.md), and `AI_PROMPTS/00_MASTER_RULES.md`):

1. **PostgreSQL 16 + PostGIS 3.4** remains the authoritative production engine executing native spatial math (`ST_Covers`, geofence boundary transitions, geodesic cross-track calculations, and ACID state machine transitions).
2. **MongoDB (`mongodb://localhost:27017/Kiroshi`)** serves as the localized developer document database, providing intuitive JSON document inspection, schema validation, flexible ad-hoc querying in MongoDB Compass, and high-volume offline event ingestion mirroring.

---

## 2. Collections Overview

The database contains **14 dedicated collections** matching all KIROSHI domain entities:

| Collection Name | Primary Purpose | Key Indexes | Spatial Index |
| :--- | :--- | :--- | :--- |
| **`users`** | Identity, authentication, and RBAC roles | `email` (Unique), `role` | — |
| **`tourist_profiles`** | Emergency contacts, medical notes, passport hashes | `user_id` (Unique) | — |
| **`trips`** | Tourist trip plans, lifecycles, emergency statuses | `(tourist_id, status)` | — |
| **`itineraries`** | Sequential destination waypoints | `(trip_id, sequence_order)` | — |
| **`geo_zones`** | Safety boundaries (`SAFE`, `RESTRICTED`, `HIGH_RISK`) | `name` (Unique) | `geometry` (2dsphere) |
| **`location_events`** | Real-time and synchronized GPS telemetry breadcrumbs | `(tourist_id, recorded_at)`, `(trip_id, recorded_at)` | `location` (2dsphere) |
| **`zone_events`** | Edge-triggered boundary `ENTER` and `EXIT` transitions | `(tourist_id, occurred_at)` | — |
| **`tourist_zone_states`** | Current spatial containment state | `(tourist_id, zone_id)` | — |
| **`risk_assessments`** | Explainable multi-factor safety risk assessments | `(tourist_id, evaluated_at)` | — |
| **`incidents`** | Authoritative 9-state life-safety emergency incidents | `idempotency_key` (Unique), `(status, severity)` | — |
| **`incident_events`** | Append-only chronological audit timeline | `(incident_id, created_at)` | — |
| **`incident_assignments`**| Field responder dispatches and reassignments | `(incident_id, responder_id)` | — |
| **`notifications`** | In-app alerts, push dispatch status, delivery tracking | `recipient_id`, `idempotency_key` (Unique) | — |
| **`sync_records`** | v0.5 Offline synchronization idempotency registry | `idempotency_key` (Unique), `(user_id, created_at)` | — |

---

## 3. Geospatial Indexing (GeoJSON WGS 84)

All spatial entities are stored in standard **GeoJSON (EPSG:4326)** format with native MongoDB `2dsphere` indexes:

### `geo_zones` (Polygon / MultiPolygon):
```json
{
  "id": "8f3b7b20-...",
  "name": "Mount Fuji Base Camp Safe Zone",
  "zone_type": "SAFE",
  "risk_multiplier": 1.0,
  "is_active": true,
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [138.720, 35.350],
        [138.740, 35.350],
        [138.740, 35.370],
        [138.720, 35.370],
        [138.720, 35.350]
      ]
    ]
  }
}
```

### `location_events` (Point):
```json
{
  "id": "d4a7f281-...",
  "tourist_id": "c1f72922-...",
  "trip_id": "b3e94a82-...",
  "latitude": 35.3606,
  "longitude": 138.7274,
  "accuracy": 8.0,
  "altitude": 2800.0,
  "speed": 1.2,
  "heading": 45.0,
  "location": {
    "type": "Point",
    "coordinates": [138.7274, 35.3606]
  },
  "recorded_at": "2026-09-05T09:40:00.000Z",
  "received_at": "2026-09-05T09:40:01.200Z"
}
```

---

## 4. How to Connect & Query in MongoDB

### MongoDB Compass Connection:
Enter the URI:
```text
mongodb://localhost:27017/Kiroshi
```

### Geospatial Proximity Query Example (`$near`):
Find all location telemetry points recorded within 500 meters of a coordinate:
```javascript
db.location_events.find({
  location: {
    $near: {
      $geometry: {
        type: "Point",
        coordinates: [138.7274, 35.3606]
      },
      $maxDistance: 500
    }
  }
});
```

### Geofence Containment Query (`$geoIntersects`):
Find which GeoZone contains a tourist's GPS point:
```javascript
db.geo_zones.find({
  geometry: {
    $geoIntersects: {
      $geometry: {
        type: "Point",
        coordinates: [138.7250, 35.3550]
      }
    }
  }
});
```

### Idempotency Check (v0.5 Sync Records):
```javascript
db.sync_records.findOne({ idempotency_key: "sos-1725529800-5678" });
```

---

## 5. Re-running the Migration Script

To refresh collections, re-apply JSON Schema validators, or re-seed sample data, run:

```powershell
.venv\Scripts\python.exe scripts/migrate_to_mongodb.py
```
*(This script is strictly isolated to the `mongodb://localhost:27017/Kiroshi` database and does not affect global MongoDB server configuration).*
