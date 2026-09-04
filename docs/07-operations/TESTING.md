# Testing Strategy & Execution — KIROSHI

> Status: IMPLEMENTED (v0.1)

---

## 1. Testing Philosophy

Per Master Rule #8:
- Every meaningful feature must have automated tests.
- Failure paths, security boundaries, and authorization checks must be tested alongside happy paths.
- Never claim tests pass without executing them.

---

## 2. Test Suites

### 2.1 Backend Tests (`backend/tests/`)
- `test_auth.py`: User registration, unique email constraint enforcement, login password verification, JWT generation, invalid token handling.
- `test_authorization.py`: Multi-role access control; ensures tourists cannot access other tourists' profiles or trips (IDOR protection).
- `test_authority_access.py`: Ensures authorities can inspect all active trips and authorized tourist profiles.
- `test_trips.py`: Trip creation, itinerary waypoint linkage, trip state transitions (`PLANNED` -> `ACTIVE` -> `COMPLETED`).
- `test_health.py`: System health check endpoint format and status.

### Execution Command
```powershell
.venv\Scripts\python -m pytest backend/tests -v
```

---

## 3. Test Coverage Goals

- Backend unit & API: >= 85% on service, domain, and security components.
- Authorization coverage: 100% of non-public endpoints tested for unauthorized (401) and forbidden (403) states.
