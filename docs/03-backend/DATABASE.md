# Database Design — KIROSHI v0.1

> Status: IMPLEMENTED (v0.1)

---

## 1. Engine & Migration Strategy

- **ORM**: SQLAlchemy 2.0 with declarative mapped columns.
- **Migration Manager**: Alembic with versioned scripts in `backend/alembic/versions/`.
- **Target Database**: PostgreSQL 16 + PostGIS 3.4.
- **Local Dev / Test Database**: SQLite (WAL mode, foreign keys explicitly enabled via connection listeners).

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
