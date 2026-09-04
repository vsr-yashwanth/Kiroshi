# System Design — KIROSHI v0.1

> Status: IMPLEMENTED (v0.1)

---

## 1. Domain Entities & Data Modeling

The core platform centers around four primary entities:

```mermaid
erDiagram
    USER ||--o| TOURIST_PROFILE : "has profile"
    USER ||--o{ TRIP : "owns"
    TRIP ||--o{ ITINERARY : "contains"

    USER {
        uuid id PK
        string email UK
        string hashed_password
        string full_name
        string phone_number
        string role "TOURIST | AUTHORITY | RESPONDER | ADMIN"
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    TOURIST_PROFILE {
        uuid id PK
        uuid user_id FK, UK
        string nationality
        string passport_or_id_hash
        string emergency_contact_name
        string emergency_contact_phone
        string medical_notes
        boolean consent_given
        timestamp created_at
        timestamp updated_at
    }

    TRIP {
        uuid id PK
        uuid tourist_id FK
        string title
        string description
        timestamp start_date
        timestamp end_date
        string status "PLANNED | ACTIVE | COMPLETED | CANCELLED"
        string emergency_status "NORMAL | AT_RISK | SOS"
        timestamp created_at
        timestamp updated_at
    }

    ITINERARY {
        uuid id PK
        uuid trip_id FK
        string destination_name
        timestamp planned_arrival
        timestamp planned_departure
        float latitude
        float longitude
        int sequence_order
        timestamp created_at
    }
```

---

## 2. Component Boundaries & Responsibilities

### `backend/app/core/`
- `config.py`: Single source of truth for runtime settings (environment, secret keys, token TTLs, database URLs).
- `security.py`: Cryptographic routines (bcrypt password hashing, JWT encode/decode, token validation).
- `database.py`: SQLAlchemy engine, session maker, declarative base.
- `errors.py`: Domain-specific exceptions (`AppException`, `EntityNotFoundError`, `AuthorizationError`, `DuplicateResourceError`).
- `logging.py`: Structured logger configuration.

### `backend/app/domain/models/`
- Declarative SQLAlchemy models representing relational tables with explicit constraints, foreign keys, and indexes.

### `backend/app/schemas/`
- Pydantic models for incoming request validation and outgoing serialization.
- Separate schemas for Create, Update, and Read operations to prevent mass-assignment vulnerabilities.

### `backend/app/services/`
- **`AuthService`**: Authenticates credentials, validates unique emails, issues JWT bearer tokens.
- **`TouristService`**: Manages profile creation and retrieval, enforcing that tourists can only access their own profile while authorities can query authorized profiles.
- **`TripService`**: Manages trip lifecycles, ensures only the trip owner can start/stop their trip, and validates state transitions (`PLANNED` -> `ACTIVE` -> `COMPLETED`).

### `backend/app/api/v1/endpoints/`
- FastAPI route handlers with typed dependencies and HTTP status code mappings.
