# KIROSHI — Smart Tourist Safety Monitoring & Incident Response System

[![CI](https://github.com/vsr-yashwanth/KIROSHI/actions/workflows/ci.yml/badge.svg)](https://github.com/vsr-yashwanth/KIROSHI/actions)
[![Milestone](https://img.shields.io/badge/Milestone-v0.3.0--Intelligent--Risk--Engine-success.svg)](https://github.com/vsr-yashwanth/KIROSHI)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PostGIS](https://img.shields.io/badge/PostGIS-3.4%2B-336791.svg)](https://postgis.net/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.x-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

> **KIROSHI** (*Keypoint Intelligence for Real-time Observation, Safety & Human Interaction*) is an enterprise-grade tourist safety platform engineered to provide privacy-preserving digital identity, trip and itinerary management, real-time safety tracking, intelligent incident response, and multi-stakeholder authority coordination.

---

## Current Status: Milestone v0.3.0 — Intelligent Risk Engine

Milestone v0.3 introduces a dedicated, deterministic, explainable risk assessment engine (`v0.3-rule-engine`) to the KIROSHI platform:

- **Deterministic Rule Engine (`backend/app/engines/risk/`)**: Transparent weighted scoring model evaluating geodesic route deviation, hazard zone containment, prolonged immobility, anomalous velocity, and geofence state events without black-box machine learning.
- **Configurable Risk Thresholds**: Centralized policy mapping normalized scores $[0.0, 1.0]$ into five discrete operational tiers: `SAFE`, `LOW`, `MEDIUM`, `HIGH`, and `CRITICAL`.
- **Natural Language Explainability**: Synthesizes human-readable operational summaries explaining contributing factors for human authority verification.
- **Multi-Factor Data Confidence**: Formulates observational data quality $[0.10, 1.00]$ based on GPS accuracy, location freshness, trajectory depth, and route availability.
- **Risk Persistence (`RiskAssessment`)**: SQLAlchemy model with composite spatial/temporal indexes (`ix_risk_assessments_tourist_created`, `ix_risk_assessments_trip_created`) tracking full evaluation history.
- **Risk REST Endpoints**: Strict RBAC endpoints (`/api/v1/risk/current/{tourist_id}`, `/api/v1/risk/history/{trip_id}`, `/api/v1/risk/active`) preventing cross-tourist data leakage.
- **Real-Time WebSocket Integration**: Selective risk event broadcast (`RISK_UPDATE`) triggered upon meaningful state transitions, delivered to subscribed authority consoles.
- **Authority Risk Inspector Drawer**: Interactive React 19 UI component featuring real-time risk scores, animated hazard halos, confidence gauges, signal breakdowns, and historical risk timeline.
- **Comprehensive Automated Test Suite**: 63 automated tests passing cleanly across unit, boundary thresholds, determinism over 100 runs, API RBAC, and complete v0.3 end-to-end workflow (63/63 total passing).

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
- [x] **v0.4.0 — Emergency Response**: SOS verification, incident assignment, responder coordination.
- [x] **v0.5.0 — Offline-First**: Local event queue, offline SOS, store-and-forward sync.
- [ ] **v0.6.0 — Computer Vision**: Edge fall detection, CCTV search window assistance.
- [ ] **v0.7.0 — Audit & Trust**: Cryptographic tamper-evident incident logging.
- [ ] **v1.0.0 — Production Release**: Penetration testing, load benchmarking, multi-region hardening.

---

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
