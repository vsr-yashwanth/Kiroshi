# Development Guide — KIROSHI

> Status: IMPLEMENTED (v0.1)

---

## 1. Local Environment Setup

### Python Environment Isolation
KIROSHI strictly requires that all backend dependencies reside inside `.venv`.
```powershell
# Create venv if not present
python -m venv .venv

# Activate in PowerShell
.venv\Scripts\Activate.ps1

# Verify executable path points to .venv
python -c "import sys; print(sys.executable)"

# Install dependencies inside .venv
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

### Dashboard Environment Isolation
```bash
cd apps/dashboard
npm install
npm run dev
```

---

## 2. Database Workflow

### Local Development (Zero-Dependency SQLite)
By default in local mode, `.env` points to `sqlite:///./kiroshi.db`.
To run migrations:
```bash
cd backend
alembic upgrade head
```

### PostgreSQL / PostGIS (Docker)
When Docker is available:
```bash
docker compose -f infrastructure/docker/docker-compose.yml up -d db
```
Update `DATABASE_URL` in `.env`:
```text
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/kiroshi
```
Then run migrations:
```bash
cd backend
alembic upgrade head
```

---

## 3. Running Backend Locally
```bash
.venv\Scripts\python -m uvicorn backend.app.main:app --reload --port 8000
```
Interactive documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).
