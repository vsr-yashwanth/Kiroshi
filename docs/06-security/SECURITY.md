# Security Architecture & Policies — KIROSHI

> Status: UPDATED (v0.7 Advanced Audit & Trust)

---

## 1. Threat Model & Mitigations

| Threat | Attack Vector | Mitigation in KIROSHI |
|---|---|---|
| **Insecure Direct Object Reference (IDOR)** | Tourist modifies `trip_id` or `user_id` to read or cancel another traveler's journey | Server-side authorization explicitly checks resource ownership (`trip.tourist_id == current_user.id`). |
| **Credential Compromise** | Rainbow tables or database leaks | Passwords salted and hashed with bcrypt (cost 12). Plaintext never logged. |
| **Session Hijacking** | Intercepted tokens | Short-lived JWT access tokens; HTTPS enforced in non-local environments; tokens transmitted via Authorization Bearer headers. |
| **Privilege Escalation** | Client self-declares role as `ADMIN` or `AUTHORITY` | Role is stored server-side and encoded in cryptographically signed JWT. Modification invalidates token signature. |
| **Injection Attacks** | SQL injection via API parameters | Parameterized queries enforced through SQLAlchemy ORM 2.0. Direct string query formatting is forbidden. |
| **Credential Leakage in Repo** | Accidental commit of secrets | Strict `.gitignore` covering `.env`, keys, and tokens. Continuous testing against `.env.example`. |
| **Incident IDOR / Scope Leakage** | Responder/Tourist attempts to read or mutate unrelated incidents | Strict server-side tenancy: Responders can only view and update incidents assigned to them; Tourists are restricted to their own incidents. |
| **State Machine Bypassing** | Attacker attempts to jump states (e.g. DETECTED -> RESOLVED) | Authoritative server-side `IncidentStateMachine` rejects invalid and unauthorized transitions with 400/403. |
| **SOS Triage Exhaustion** | Rapid-fire duplicate SOS submissions overloading dispatchers | Client-generated `idempotency_key` with database uniqueness constraints suppresses duplicate submissions. |
| **Audit Log Tampering & History Forgery** | Attacker attempts to rewrite historical incident events or dismissals | v0.7 Cryptographic Hash Chaining: SHA-256 forward pointers anchor all `audit_events`. `AuditChainVerifier` detects any modification, deletion, or reordering. |
| **Unauthorized Audit Access & Data Exfiltration** | Attacker tries to read security logs or export tourist audit records | RBAC strictly limits `/api/v1/audit/*` endpoints to `ADMIN` and `AUTHORITY` roles. All data exports generate an audited event trace. |

---

## 2. Server-Side Enforcement Rules

1. Never trust the client for authorization.
2. Never store private keys or API secrets in source control.
3. Keep CORS origins restricted to approved dashboard/mobile domains.
4. Redact PII in server application logs and audit event details.
5. Critical emergency paths (SOS) must remain operational when AI/ML or external notification/trust infrastructure is down.
6. Incident state machine transitions are strictly authoritative on the server.
7. Audit event hashes are calculated deterministically using canonical JSON serialization with UTC timestamps.
8. Audit chain verification is available to administrators and authorized authorities to ensure tamper evidence.

---

## 3. Cryptographic Verification & Trust Layer (v0.7)

- **Algorithm**: Standardized `SHA-256` hashing on canonical JSON event payloads.
- **Genesis Block**: Root anchored at 64 zeroes (`0000000000000000000000000000000000000000000000000000000000000000`).
- **Chain Continuity**: Every event `N+1` contains `previous_hash = event_N.event_hash`.
- **Integrity Status**: Verifiable dynamically via `POST /api/v1/audit/verify` returning `CHAIN_VALID` or `CHAIN_BROKEN`.
