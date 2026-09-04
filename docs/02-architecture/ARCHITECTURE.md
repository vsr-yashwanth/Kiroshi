# Architecture Overview — KIROSHI

> Status: IMPLEMENTED (v0.1) | Architectural Pattern: Modular Monolith

---

## 1. Architectural Philosophy

KIROSHI avoids artificial complexity. Instead of adopting microservices or distributed message brokers prematurely, KIROSHI implements a **well-structured modular monolith**. This provides:
- Single deployment unit with clear internal module boundaries.
- Zero distributed network failure modes for internal service calls.
- Strict dependency direction: Controllers depend on Services; Services depend on Domain Entities and Repositories; Repositories depend on Database abstractions.
- Clear migration paths: Individual domains (e.g., Risk Engine, Incident Service) can be extracted into standalone services in later milestones if operational scale warrants it.

---

## 2. Layered Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                    API Controller Layer                 │
│              (FastAPI Routes, Pydantic DTOs)            │
└────────────────────────────┬────────────────────────────┘
                             │ calls
┌────────────────────────────▼────────────────────────────┐
│                    Application Services                 │
│         (AuthService, TouristService, TripService)      │
└────────────────────────────┬────────────────────────────┘
                             │ calls
┌────────────────────────────▼────────────────────────────┐
│                  Domain Model & Entities                │
│             (User, TouristProfile, Trip, Itinerary)     │
└────────────────────────────┬────────────────────────────┘
                             │ calls
┌────────────────────────────▼────────────────────────────┐
│                   Data Persistence Layer                │
│              (SQLAlchemy 2.0 ORM, Repositories)         │
└────────────────────────────┬────────────────────────────┘
                             │ persists
┌────────────────────────────▼────────────────────────────┐
│                     Relational Database                 │
│                 (PostgreSQL 16 / SQLite WAL)            │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Technology Choices & Justification

| Layer | Chosen Technology | Justification |
|---|---|---|
| **Backend Framework** | FastAPI (Python 3.10+) | High performance ASGI async engine, native Pydantic type safety, automatic OpenAPI documentation generation. |
| **ORM & Migrations** | SQLAlchemy 2.0 + Alembic | Declarative mapping, explicit session control, clean database abstraction, robust versioned migrations. |
| **Primary Database** | PostgreSQL 16 + PostGIS 3.4 | Industry-standard relational integrity with geospatial querying capabilities required for geo-fencing in v0.2. |
| **Local DB Fallback** | SQLite (WAL Mode) | Zero-friction local development and automated testing without requiring external Docker daemons on host machines. |
| **Authority Portal** | React 19 + TypeScript + Vite | Static typed component architecture, fast build times, responsive modern UI. |
| **Mobile Client** | Flutter / Dart | Single cross-platform codebase for iOS and Android with high-performance native rendering. |

---

## 4. Cross-Cutting Concerns

- **Security & RBAC**: Injected via FastAPI dependencies (`get_current_user`, `require_role`).
- **Database Sessions**: Managed using scoped generator dependencies (`get_db`) ensuring rollback on unhandled exceptions.
- **Error Handling**: Centralized exception handler mapping domain errors to standard RFC 7807 problem details.
- **Logging**: Structured JSON/formatted logging capturing timestamp, level, module, and request traces.
