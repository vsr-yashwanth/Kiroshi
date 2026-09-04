# ADR-001 — Adoption of Modular Monolith Architecture

## Status
Accepted

## Context
KIROSHI requires high cohesion across authentication, tourist profile verification, trip management, and authority oversight. While modern distributed architectures (microservices, service meshes, distributed message queues) are often touted, introducing them at this phase would add substantial networking overhead, distributed transaction complexity, deployment fragility, and operational friction.

## Options Considered
1. **Microservices Architecture**: Separate services for Auth, Tourists, Trips, and Authority.
2. **Modular Monolith**: Single deployable FastAPI backend structured internally with strict domain boundaries and layered architecture.
3. **Unstructured Script Monolith**: Flat application with tightly coupled routes and queries.

## Decision
Adopt a **Modular Monolith** architecture implemented in Python with FastAPI, SQLAlchemy 2.0, and Pydantic.

## Rationale
- High developer velocity and single-command local setup.
- Enforces domain boundaries via code structure (`app/core`, `app/domain`, `app/services`, `app/repositories`, `app/api`).
- Retains transaction atomicity across database tables without two-phase commit overhead.
- Enables frictionless future decomposition into microservices if scaling requirements genuinely demand it.

## Consequences
- Requires discipline to prevent circular imports or bleeding business logic into API controllers.
- Requires strict dependency injection patterns.

## Rejected Alternatives
- Microservices rejected as premature optimization introducing unnecessary operational failure modes.
