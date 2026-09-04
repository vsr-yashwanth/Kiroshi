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

---

## 4. Milestone Git Branching Strategy

For each KIROSHI milestone, strict branch isolation is enforced:

1. **Create Dedicated Feature Branch**: Always branch off the latest verified `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/v0.X-<milestone-slug>
   ```
2. **Feature-Branch-Only Commits**: All implementation, test additions, and documentation for that milestone must occur on that dedicated feature branch. Never commit milestone development directly to `main`.
3. **Acceptance & Non-Fast-Forward Merge**: Once all milestone acceptance criteria and test suites pass 100%:
   ```bash
   git checkout main
   git merge --no-ff feature/v0.X-<milestone-slug> -m "Merge branch 'feature/v0.X-<milestone-slug>' into main"
   ```
4. **Tagging & Remote Sync**: Create the semantic version tag on the merge commit, and push both the feature branch and `main` with tags:
   ```bash
   git tag -a v0.X.0 -m "Release v0.X.0 - <Milestone Title>"
   git push origin main feature/v0.X-<milestone-slug> --tags
   ```
5. **Next Milestone Inception**: Only start work on the subsequent milestone after the prior milestone is cleanly merged and tagged on `main`.
