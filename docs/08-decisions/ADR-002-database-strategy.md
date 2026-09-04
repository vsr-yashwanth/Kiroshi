# ADR-002 — Relational Storage & Database Strategy

## Status
Accepted

## Context
KIROSHI requires strong consistency and relational integrity for user accounts, profiles, trips, and itineraries. Furthermore, future milestones (v0.2+) require advanced geospatial operations (spatial indexing, polygon containment, route deviation). At the same time, local developer ergonomics must allow seamless onboarding and automated test execution even on developer workstations lacking running Docker daemons.

## Options Considered
1. **PostgreSQL 16 + PostGIS Exclusively**: Require running Postgres instances for every developer test and run.
2. **MongoDB / Document Store**: Flexible document storage.
3. **Dual Dialect SQLAlchemy Abstraction**: Target PostgreSQL 16 + PostGIS for production & container infrastructure, with native SQLite fallback for local development and test runs.

## Decision
Adopt **SQLAlchemy 2.0 with Alembic**, targeting **PostgreSQL 16 + PostGIS 3.4** as the primary production engine while supporting **SQLite (WAL mode)** for local development and zero-dependency test suites.

## Rationale
- Relational integrity is mandatory for security, RBAC, and trip lifecycles.
- PostGIS provides the necessary spatial foundation for v0.2 without requiring separate geospatial databases.
- The dual-dialect approach allows instant automated testing and local execution without mandatory Docker daemon availability.

## Consequences
- Table definitions must avoid dialect-specific non-standard features or wrap them in dialect conditionals.
- Milestone v0.2.0 spatial tests will require the Docker PostGIS container to exercise spatial index queries.

## Rejected Alternatives
- Document databases rejected due to lack of strict relational constraints and inferior spatial index standards compared to PostGIS.
