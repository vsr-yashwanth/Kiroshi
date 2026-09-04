# KIROSHI — Smart Tourist Safety Monitoring & Incident Response System

[![CI](https://github.com/vsr-yashwanth/KIROSHI/actions/workflows/ci.yml/badge.svg)](https://github.com/vsr-yashwanth/KIROSHI/actions)
[![Milestone](https://img.shields.io/badge/Milestone-v0.1.0--Core--Platform-blue.svg)](https://github.com/vsr-yashwanth/KIROSHI)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.x-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

> **KIROSHI** (*Keypoint Intelligence for Real-time Observation, Safety & Human Interaction*) is an enterprise-grade tourist safety platform engineered to provide privacy-preserving digital identity, trip and itinerary management, real-time safety tracking, intelligent incident response, and multi-stakeholder authority coordination.

---

## Current Status: Milestone v0.1.0 — Core Platform

This milestone establishes the verified foundational core of KIROSHI:

- **Clean Backend Monolith (FastAPI)**: Layered architecture (API, Services, Domain, Repositories, Database).
- **Relational Data Foundation (SQLAlchemy 2.0 + Alembic)**: UUID primary keys, strict foreign key constraints, timestamps, and indexing. Configured for PostgreSQL/PostGIS with resilient local SQLite fallback.
- **Server-Enforced Authentication & Authorization**: Argon2/Bcrypt password hashing, JWT bearer tokens, and server-enforced role access controls (`TOURIST`, `AUTHORITY`, `RESPONDER`, `ADMIN`). Cross-tenant and IDOR protected.
- **Trip Lifecycle Management**: Tourists can create trips, define itinerary waypoints, and transition trips through state machines (`PLANNED` -> `ACTIVE` -> `COMPLETED`).
- **Authority Command Portal (React + TypeScript)**: Dedicated web portal for tourism authorities to inspect verified tourist profiles, active trips, and system metrics.
- **Mobile Client Architecture (Flutter / Dart)**: Domain-driven clean architecture specification for the tourist client app.
- **Comprehensive Test Suite**: Automated unit, security, integration, and API tests executed via `pytest`.

---

## Repository Structure

```text
KIROSHI/
│
├── apps/
│   ├── mobile/             # Flutter tourist mobile application
│   └── dashboard/          # React + TypeScript authority dashboard
│
├── backend/
│   ├── app/                # FastAPI application (API, Core, Domain, Services, Repos)
│   ├── tests/              # Backend automated test suite
│   ├── alembic/            # Alembic database migration scripts
│   └── requirements.txt    # Python backend dependencies
│
├── ml/                     # ML pipelines & models (Planned for v0.6)
│
├── infrastructure/
│   ├── docker/             # Docker compose configurations (PostgreSQL/PostGIS)
│   ├── deployment/         # Production deployment configurations
│   └── monitoring/         # Health & metrics configuration
│
├── docs/                   # Architectural, technical, security & operational documentation
│   ├── 01-overview/
│   ├── 02-architecture/
│   ├── 03-backend/
│   ├── 04-mobile/
│   ├── 05-intelligence/
│   ├── 06-security/
│   ├── 07-operations/
│   └── 08-decisions/       # Architecture Decision Records (ADRs)
│
├── scripts/                # Local development & operational automation scripts
├── .github/workflows/      # Continuous integration workflows
├── .env.example            # Environment configuration template
└── README.md
```

---

## Getting Started

### Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: v18 or higher (v24+ recommended), npm 9+
- **Docker** (optional): For running PostgreSQL 16 with PostGIS

### 1. Backend Setup

1. **Create and activate an isolated virtual environment:**
   ```powershell
   # Windows PowerShell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
   ```bash
   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Verify isolated Python environment:**
   ```bash
   python -c "import sys; print(sys.executable)"
   # Path must point to your project .venv
   ```

3. **Install dependencies:**
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r backend/requirements.txt
   ```

4. **Initialize Environment Configuration:**
   ```powershell
   Copy-Item .env.example .env
   ```

5. **Run Database Migrations:**
   ```bash
   cd backend
   alembic upgrade head
   cd ..
   ```

6. **Start Backend Server:**
   ```bash
   .venv\Scripts\python -m uvicorn backend.app.main:app --reload --port 8000
   ```
   - OpenAPI Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### 2. Authority Dashboard Setup

1. **Install local dependencies:**
   ```bash
   cd apps/dashboard
   npm install
   ```

2. **Start Dashboard Dev Server:**
   ```bash
   npm run dev
   ```
   - Access Dashboard: [http://localhost:5173](http://localhost:5173)

3. **Build for Production:**
   ```bash
   npm run build
   ```

---

## Running Automated Tests

Run backend unit, API, and authorization tests:
```powershell
.venv\Scripts\python -m pytest backend/tests -v
```

---

## Project Governance & Engineering Standards

KIROSHI follows the engineering contract defined in:
- [`docs/01-overview/PROJECT.md`](docs/01-overview/PROJECT.md)
- [`docs/02-architecture/ARCHITECTURE.md`](docs/02-architecture/ARCHITECTURE.md)
- [`docs/06-security/SECURITY.md`](docs/06-security/SECURITY.md)

Key principles:
1. **Zero Fake Core Logic**: All primary v0.1 workflows run against real backend services and database persistence.
2. **Server-Side Authorization**: Roles and ownership are verified exclusively on the server.
3. **Environment Isolation**: No dependencies are installed globally.
4. **Honest Documentation**: Every feature state is classified as `IMPLEMENTED`, `EXPERIMENTAL`, `PARTIALLY IMPLEMENTED`, `SIMULATED`, or `PLANNED`.

---

## Roadmap

- [x] **v0.1.0 — Core Platform**: Authentication, Profiles, Trip Management, Authority Inspection.
- [ ] **v0.2.0 — Real-Time Geospatial**: PostGIS spatial queries, location ingestion, WebSockets, live map.
- [ ] **v0.3.0 — Risk Engine**: Multi-signal anomaly detection, route deviation, safety scoring.
- [ ] **v0.4.0 — Emergency Response**: SOS verification, incident assignment, responder coordination.
- [ ] **v0.5.0 — Offline-First**: Local event queue, offline SOS, store-and-forward sync.
- [ ] **v0.6.0 — Computer Vision**: Edge fall detection, CCTV search window assistance.
- [ ] **v0.7.0 — Audit & Trust**: Cryptographic tamper-evident incident logging.
- [ ] **v1.0.0 — Production Release**: Penetration testing, load benchmarking, multi-region hardening.

---

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
