# Security Architecture & Policies — KIROSHI

> Status: IMPLEMENTED (v0.1)

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

---

## 2. Server-Side Enforcement Rules

1. Never trust the client for authorization.
2. Never store private keys or API secrets in source control.
3. Keep CORS origins restricted to approved dashboard/mobile domains.
4. Redact PII in server application logs.
