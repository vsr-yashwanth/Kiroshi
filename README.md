# KIROSHI — Smart Tourist Safety Monitoring & Incident Response System

[![CI](https://github.com/vsr-yashwanth/KIROSHI/actions/workflows/ci.yml/badge.svg)](https://github.com/vsr-yashwanth/KIROSHI/actions)
[![Milestone](https://img.shields.io/badge/Milestone-v0.4.0--Emergency--Response-success.svg)](https://github.com/vsr-yashwanth/KIROSHI)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PostGIS](https://img.shields.io/badge/PostGIS-3.4%2B-336791.svg)](https://postgis.net/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.x-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

> **KIROSHI** (*Keypoint Intelligence for Real-time Observation, Safety & Human Interaction*) is an enterprise-grade tourist safety platform engineered to provide privacy-preserving digital identity, trip and itinerary management, real-time safety tracking, intelligent incident response, and multi-stakeholder authority coordination.

---

## Current Status: Milestone v0.4.0 — Emergency Response & Incident Management

Milestone v0.4 introduces an enterprise incident management domain, a life-critical emergency SOS beacon, a strict 9-state server-side transition state machine, and real-time authority dispatch operations:

- **Independent Incident Domain (`backend/app/domain/models/incident*.py`)**: Independent lifecycle entities (`Incident`, `IncidentEvent`, `IncidentAssignment`) decoupled from analytical risk scoring.
- **Server-Enforced 9-State State Machine (`IncidentStateMachine`)**: Rigidly enforces transition matrix across `DETECTED`, `VERIFYING`, `VERIFIED`, `ESCALATED`, `ASSIGNED`, `RESPONDING`, `RESOLVED`, `CLOSED`, and `DISMISSED`. Terminal states are immutable.
- **Role-Aware Transition Security**: Strict RBAC prevents unauthorized mutations (tourists cannot resolve, responders cannot close, responders can only update assigned incidents).
- **Life-Critical Emergency SOS Beacon**: 100% decoupled from AI, ML, CCTV, and external gateways. Automatically captures GPS with `LIVE` / `RECENT` / `STALE` freshness, gracefully falling back to `UNKNOWN` if GPS is disabled without blocking incident creation.
- **SOS Idempotency Protection**: Client-generated idempotency keys suppress double-taps and network retransmissions.
- **Append-Only Timeline Audit Trail**: Every status change, assignment, and escalation generates an immutable `IncidentEvent` record with actor, role, timestamps, and rationale.
- **Pluggable Notification Abstraction**: In-app provider with delivery retry and guaranteed failure isolation (notification errors never roll back incident creation).
- **Real-Time WebSocket Incident Pipeline**: Extends `/api/v1/ws/authority` with `INCIDENT_CREATED`, `INCIDENT_STATUS_CHANGED`, and `INCIDENT_ASSIGNED` broadcasts.
- **Authority Incident Operations Console**: React 19 dashboard featuring real-time queue counters, severity indicators, status filters, responder assignment, and chronological timeline view.
- **Comprehensive Automated Test Suite**: 79 automated tests passing cleanly across state machine transitions, invalid terminal rejection, SOS failure modes, notifications, API access control, and complete end-to-end emergency lifecycle (79/79 passing).

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
- [x] **v0.2.0 — Real-Time Geospatial**: PostGIS spatial queries, location ingestion, WebSockets, live map.
- [x] **v0.3.0 — Risk Engine**: Multi-signal anomaly detection, route deviation, safety scoring.
- [ ] **v0.4.0 — Emergency Response**: SOS verification, incident assignment, responder coordination.
- [ ] **v0.5.0 — Offline-First**: Local event queue, offline SOS, store-and-forward sync.
- [ ] **v0.6.0 — Computer Vision**: Edge fall detection, CCTV search window assistance.
- [ ] **v0.7.0 — Audit & Trust**: Cryptographic tamper-evident incident logging.
- [ ] **v1.0.0 — Production Release**: Penetration testing, load benchmarking, multi-region hardening.

---

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
