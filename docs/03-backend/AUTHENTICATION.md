# Authentication & Authorization — KIROSHI v0.1

> Status: IMPLEMENTED (v0.1)

---

## 1. Authentication Architecture

KIROSHI adopts an industry-standard token-based authentication mechanism:
- **Password Storage**: Passwords are never stored in plaintext. They are salted and hashed using `bcrypt` (work factor 12).
- **Session Tokens**: Cryptographically signed JSON Web Tokens (`HS256` in development; configurable for asymmetric `RS256` in production).
- **Transport Security**: All authentication exchanges require HTTPS in non-local environments.

---

## 2. Role-Based Access Control (RBAC)

The system supports four distinct operational roles:

```text
ADMIN
  │
  ├── AUTHORITY (Tourism department, emergency command center)
  │
  ├── RESPONDER (Field rescue teams, medical personnel)
  │
  └── TOURIST   (End-user civilian travelers)
```

### Access Matrix

| Resource / Action | `TOURIST` | `AUTHORITY` | `RESPONDER` | `ADMIN` |
|---|---|---|---|---|
| Register / Login | Yes | Yes | Yes | Yes |
| Manage Own Profile | Yes | Yes | Yes | Yes |
| View Other Tourist Profiles | **No** | **Yes** | **Yes** | **Yes** |
| Create / Manage Own Trips | Yes | No | No | Yes |
| View Active Trips Fleet | **No** | **Yes** | **Yes** | **Yes** |
| Start / Stop Own Trip | Yes | No | No | Yes |
| Emergency Intervene / Stop Trip | No | **Yes** | **Yes** | **Yes** |

---

## 3. Server-Side Enforcement (Defense Against IDOR)

A common vulnerability in prototype systems is trusting client-supplied identifiers (e.g. modifying `tourist_id` or `trip_id` in request payloads).

KIROSHI strictly prevents this:
1. When a user requests `/api/v1/tourists/me`, the identity is resolved strictly from the decoded JWT claims (`sub` field).
2. When a user accesses `/api/v1/trips/{id}`, the backend asserts:
   ```python
   if current_user.role == UserRole.TOURIST and trip.tourist_id != current_user.id:
       raise HTTPException(status_code=403, detail="Not authorized to access this trip")
   ```
3. Role checks are executed before database queries using FastAPI dependency injection (`require_role(...)`).
