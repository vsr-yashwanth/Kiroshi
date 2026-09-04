# Changelog

All notable changes to the KIROSHI platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] — 2026-09-04

### Added
- **Repository Architecture**: Initialized repository structure following domain-driven modular monolith guidelines.
- **Environment Isolation**: Configured Python `.venv` management and project-local Node dependency governance.
- **Backend Architecture**: Layered FastAPI backend with clean separation of concerns (`api/`, `core/`, `domain/`, `services/`, `repositories/`).
- **Database Schema**: Established SQLAlchemy 2.0 models and Alembic migrations for `User`, `TouristProfile`, `Trip`, and `Itinerary`.
- **Authentication**: JWT token issuance, verification, and bcrypt password hashing.
- **Server-Side Authorization**: Role-based access control supporting `TOURIST`, `AUTHORITY`, `RESPONDER`, and `ADMIN`.
- **Trip Lifecycle API**: Endpoints for trip creation, itinerary waypoint specification, trip start, and trip stop with status tracking.
- **Authority Dashboard**: React 19 + TypeScript + Vite web application for authorities to view tourists, active trips, and system health.
- **Flutter Mobile Foundation**: Mobile architecture specification with Domain, Application, Presentation, and Infrastructure layers.
- **Automated Testing Suite**: Automated pytest suite covering authentication, ownership validation, authorization, and trip state machines.
- **Documentation**: Comprehensive technical documentation suite across overview, architecture, backend, mobile, security, and operations.

### Security
- Server-side authorization preventing IDOR (Insecure Direct Object Reference) on tourist profile and trip resources.
- Strict password hashing via bcrypt with configurable salt rounds.
- Environment-based secret configuration via `.env` (gitignored).

### Known Limitations
- Real-time WebSockets and live GPS streaming are deferred to v0.2.0.
- Machine learning risk engine is deferred to v0.3.0.
- Flutter SDK is not installed on the current host machine; mobile test execution is deferred to a CI environment or an SDK-equipped workstation.
