# Contributing to KIROSHI

Thank you for your interest in contributing to KIROSHI.

KIROSHI is a serious engineering project intended for portfolio and long-term production use. All contributions must adhere to the engineering rules outlined in [`docs/01-overview/PROJECT.md`](docs/01-overview/PROJECT.md) and [`docs/02-architecture/ARCHITECTURE.md`](docs/02-architecture/ARCHITECTURE.md).

---

## 1. Core Engineering Principles

1. **Environment Isolation**: Always use project-isolated environments (`.venv` for Python, local `node_modules` for Node). Never install dependencies globally.
2. **Layered Architecture**: Respect domain boundaries:
   ```text
   API Controller -> Service Layer -> Domain Entities / Repositories -> Database
   ```
   Do not leak business logic into API endpoints or UI views.
3. **Zero Fake Core Functionality**: Never use static/mock data for core primary workflows. Real backend services and database persistence are required.
4. **Server-Side Authorization**: Clients must never be trusted for access control. Always enforce authorization and ownership on the backend.
5. **Testing**: Every PR that introduces or modifies functionality must include tests covering happy paths, failure modes, and security boundaries.
6. **Documentation Synchronization**: When modifying code, update corresponding documentation (`docs/`) in the same pull request.

---

## 2. Development Workflow

1. Create a focused branch:
   ```bash
   git checkout -b feat/trip-management
   # or fix/auth-token-expiry
   ```
2. Write clean code following PEP 8 (Python) and ESLint/Prettier (TypeScript).
3. Run automated tests before committing:
   ```bash
   .venv\Scripts\python -m pytest backend/tests
   cd apps/dashboard && npm test
   ```
4. Commit using Conventional Commits:
   ```text
   feat(trips): add waypoint sequence validation
   fix(auth): invalidate expired refresh tokens
   docs(api): document query parameters for trip filtering
   ```
5. Open a pull request against `main` with a clear description of changes, tests executed, and security considerations.
