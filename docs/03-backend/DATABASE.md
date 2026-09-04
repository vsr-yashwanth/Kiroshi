# Database Design — KIROSHI v0.3

> Status: IMPLEMENTED (v0.3)

---

## 1. Engine & Migration Strategy

- **ORM**: SQLAlchemy 2.0 with declarative mapped columns and GeoAlchemy2.
- **Migration Manager**: Alembic with versioned scripts in `backend/migrations/versions/`.
- **Target Database**: PostgreSQL 16 + PostGIS 3.4.
- **Spatial Geometry**: WGS84 EPSG:4326 Point & Polygon geometries indexed with PostgreSQL GIST.
- **Local Dev / Test Database**: SQLite dual-engine compatibility with in-memory Shapely spatial function bindings (`ST_Covers`, `ST_SetSRID`, `AsEWKB`, `GeomFromEWKT`).

---

## 2. Table Specifications

### 2.1 `users`
Stores system accounts across all roles.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | RFC 4122 v4 UUID |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | Login identifier |
| `hashed_password` | VARCHAR(255) | NOT NULL | Bcrypt hash |
| `full_name` | VARCHAR(255) | NOT NULL | Display name |
| `phone_number` | VARCHAR(50) | NULLABLE | Contact telephone |
| `role` | VARCHAR(50) | NOT NULL, DEFAULT 'TOURIST' | TOURIST, AUTHORITY, RESPONDER, ADMIN |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Account state |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Modification timestamp |

### 2.2 `tourist_profiles`
Stores tourist safety context and emergency information.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | RFC 4122 v4 UUID |
| `user_id` | UUID | FOREIGN KEY (`users.id` ON DELETE CASCADE), UNIQUE | Associated user |
| `nationality` | VARCHAR(100) | NULLABLE | Nationality |
| `passport_or_id_hash` | VARCHAR(255) | NULLABLE | Anonymized ID hash |
| `emergency_contact_name` | VARCHAR(255) | NULLABLE | Next of kin |
| `emergency_contact_phone`| VARCHAR(50) | NULLABLE | Next of kin contact |
| `medical_notes` | TEXT | NULLABLE | Critical allergies/conditions |
| `consent_given` | BOOLEAN | NOT NULL, DEFAULT FALSE | Digital consent |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Modification timestamp |

### 2.3 `trips`
Tracks active and planned tourist journeys.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | RFC 4122 v4 UUID |
| `tourist_id` | UUID | FOREIGN KEY (`users.id` ON DELETE CASCADE), INDEX | Owner user |
| `title` | VARCHAR(255) | NOT NULL | Journey title |
| `description` | TEXT | NULLABLE | Notes/details |
| `start_date` | TIMESTAMP WITH TIME ZONE | NOT NULL | Scheduled start |
| `end_date` | TIMESTAMP WITH TIME ZONE | NOT NULL | Scheduled conclusion |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT 'PLANNED', INDEX | PLANNED, ACTIVE, COMPLETED, CANCELLED |
| `emergency_status` | VARCHAR(50) | NOT NULL, DEFAULT 'NORMAL' | NORMAL, AT_RISK, SOS |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Modification timestamp |

### 2.4 `itineraries`
Sequential waypoints comprising a trip plan.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | RFC 4122 v4 UUID |
| `trip_id` | UUID | FOREIGN KEY (`trips.id` ON DELETE CASCADE), INDEX | Parent trip |
| `destination_name` | VARCHAR(255) | NOT NULL | Waypoint name |
| `planned_arrival` | TIMESTAMP WITH TIME ZONE | NULLABLE | ETA |
| `planned_departure` | TIMESTAMP WITH TIME ZONE | NULLABLE | ETD |
| `latitude` | DOUBLE PRECISION | NOT NULL | Decimal latitude |
| `longitude` | DOUBLE PRECISION | NOT NULL | Decimal longitude |
| `sequence_order` | INTEGER | NOT NULL | Waypoint order index |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Creation timestamp |

---

## 3. Geospatial Tables (v0.2 Additions)

### 3.1 `location_events`
Stores immutable breadcrumb GPS telemetry records ingested from mobile clients.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | RFC 4122 v4 UUID |
| `tourist_id` | UUID | FOREIGN KEY (`users.id` ON DELETE CASCADE), NOT NULL, INDEX | Tourist identifier |
| `trip_id` | UUID | FOREIGN KEY (`trips.id` ON DELETE CASCADE), NOT NULL, INDEX | Associated trip |
| `latitude` | DOUBLE PRECISION | NOT NULL | Decimal latitude (-90.0 to 90.0) |
| `longitude` | DOUBLE PRECISION | NOT NULL | Decimal longitude (-180.0 to 180.0) |
| `altitude` | DOUBLE PRECISION | NULLABLE | Elevation in meters |
| `accuracy` | DOUBLE PRECISION | NOT NULL | GPS horizontal accuracy radius (m) |
| `speed` | DOUBLE PRECISION | NULLABLE | Ground speed in m/s |
| `bearing` | DOUBLE PRECISION | NULLABLE | Heading in degrees (0.0 to 360.0) |
| `recorded_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, INDEX | Timestamp reported by GPS hardware |
| `received_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Timestamp received at API server |
| `location_point` | GEOMETRY(POINT, 4326) | NOT NULL | PostGIS Point geometry |

**Spatial Indexes:**
- `idx_location_events_point`: GIST index on `location_point` for spatial distance/bounding box queries.
- `idx_location_events_tourist_rec`: B-tree composite index on `(tourist_id, recorded_at DESC)`.
- `idx_location_events_trip_rec`: B-tree composite index on `(trip_id, recorded_at DESC)`.

### 3.2 `geo_zones`
Stores authority-defined safety boundaries, hazard perimeters, and regulatory regions.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | RFC 4122 v4 UUID |
| `name` | VARCHAR(255) | NOT NULL, INDEX | Human-readable zone name |
| `zone_type` | VARCHAR(50) | NOT NULL, INDEX | SAFE, RESTRICTED, HIGH_RISK, CUSTOM |
| `geometry` | GEOMETRY(POLYGON, 4326) | NOT NULL | PostGIS Polygon geometry |
| `coordinates_json`| JSONB / TEXT | NOT NULL | GeoJSON array of [lat, lon] vertices |
| `description` | TEXT | NULLABLE | Operational context / hazard notes |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE, INDEX | Administrative toggle |
| `created_by` | UUID | FOREIGN KEY (`users.id` ON DELETE SET NULL), NULLABLE | Creator authority |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Modification timestamp |

**Spatial Indexes:**
- `idx_geo_zones_geometry`: GIST index on `geometry` for containment checks (`ST_Covers`).

### 3.3 `tourist_zone_states`
Maintains the current spatial occupancy state of each tourist relative to each active geozone.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | RFC 4122 v4 UUID |
| `tourist_id` | UUID | FOREIGN KEY (`users.id` ON DELETE CASCADE), NOT NULL | Tourist identifier |
| `zone_id` | UUID | FOREIGN KEY (`geo_zones.id` ON DELETE CASCADE), NOT NULL | Geozone identifier |
| `is_inside` | BOOLEAN | NOT NULL, DEFAULT FALSE | Current containment state |
| `entered_at` | TIMESTAMP WITH TIME ZONE | NULLABLE | Timestamp of most recent entry |
| `exited_at` | TIMESTAMP WITH TIME ZONE | NULLABLE | Timestamp of most recent departure |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | State transition timestamp |

**Constraints & Indexes:**
- `uq_tourist_zone`: UNIQUE constraint on `(tourist_id, zone_id)`.
- Index on `(tourist_id, is_inside)`.

### 3.4 `zone_events`
Immutable audit log of all boundary crossing events (`ENTER` / `EXIT`).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | RFC 4122 v4 UUID |
| `tourist_id` | UUID | FOREIGN KEY (`users.id` ON DELETE CASCADE), NOT NULL, INDEX | Tourist identifier |
| `zone_id` | UUID | FOREIGN KEY (`geo_zones.id` ON DELETE CASCADE), NOT NULL, INDEX | Geozone identifier |
| `event_type` | VARCHAR(50) | NOT NULL | ENTER, EXIT |
| `latitude` | DOUBLE PRECISION | NOT NULL | Crossing coordinate latitude |
| `longitude` | DOUBLE PRECISION | NOT NULL | Crossing coordinate longitude |
| `occurred_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now(), INDEX | Transition timestamp |

---

## 4. Risk Engine Schema (v0.3)

### 4.1 `risk_assessments`
Persists explainable, deterministic risk evaluations computed for tourist telemetry events.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | RFC 4122 v4 UUID |
| `tourist_id` | UUID | FOREIGN KEY (`users.id` ON DELETE CASCADE), NOT NULL | Evaluated tourist |
| `trip_id` | UUID | FOREIGN KEY (`trips.id` ON DELETE CASCADE), NOT NULL | Associated active journey |
| `location_event_id` | UUID | FOREIGN KEY (`location_events.id` ON DELETE SET NULL), NULLABLE | Triggering telemetry event |
| `risk_score` | FLOAT | NOT NULL | Normalized composite score [0.0, 1.0] |
| `risk_level` | VARCHAR(50) | NOT NULL, INDEX | SAFE, LOW, MEDIUM, HIGH, CRITICAL |
| `confidence` | FLOAT | NOT NULL | Data quality metric [0.10, 1.00] |
| `contributing_signals`| JSONB / TEXT | NOT NULL | Array of signal scores, weights & details |
| `explanation` | TEXT | NOT NULL | Human-readable operational explanation |
| `recommended_action` | VARCHAR(50) | NOT NULL | MONITOR, REVIEW, CONTACT_TOURIST, ESCALATE_FOR_HUMAN_REVIEW |
| `model_version` | VARCHAR(50) | NOT NULL | Evaluator model identifier (e.g. `v0.3-rule-engine`) |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Evaluation timestamp |

**Indexes & Performance:**
- `ix_risk_assessments_tourist_created`: B-tree composite index on `(tourist_id, created_at DESC)` for instantaneous retrieval of a tourist's latest risk state.
- `ix_risk_assessments_trip_created`: B-tree composite index on `(trip_id, created_at DESC)` for chronological timeline rendering.
- `ix_risk_assessments_level`: B-tree index on `risk_level` for rapid filtering of elevated threats.
