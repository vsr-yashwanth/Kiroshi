# KIROSHI Threat Model (v0.7)

## 1. Overview & Threat Boundaries

The KIROSHI platform safeguards tourists in high-risk zones through real-time tracking, computer vision hazard detection, and rapid emergency response. This document models threats across assets, actors, attack vectors, and implemented mitigations under the STRIDE methodology.

---

## 2. Threat Actor Profiles

| Threat Actor | Motivation | Capabilities | Target Assets |
| :--- | :--- | :--- | :--- |
| **Malicious Tourist** | Fake SOS triggers, location spoofing, privacy evasion | Client API access, mobile jailbreaking | Emergency responder resources, Geofence alerts |
| **Compromised Responder** | Unauthorized location surveillance, false incident clearance | Valid responder JWT tokens | Tourist location history, Incident status |
| **Compromised Authority / Rogue Admin** | Evidence tampering, audit alteration, unlawful surveillance | DB/API administrative privileges | Incident timelines, Audit logs, CCTV feeds |
| **External Attacker / Network Sniffer** | Credential theft, data exfiltration, service disruption | MITM, API fuzzing, credential stuffing | User passwords, JWT tokens, SOS dispatch pipeline |

---

## 3. STRIDE Threat Analysis & Mitigations

### S — Spoofing Identity
- **Threat**: Attacker sends forged location pings or triggers SOS under another tourist's identity.
- **Mitigations**:
  - Strict JWT validation (`sub` user ID verification on all location and incident endpoints).
  - Mobile sync queue includes UUID generation and cryptographic signature checks.
  - Audit logging of all authentication events (`AUTH_LOGIN_FAILURE`, `AUTH_LOGIN_SUCCESS`).

### T — Tampering with Data
- **Threat**: Malicious admin modifies database rows to hide delayed emergency response or delete incident records.
- **Mitigations**:
  - Cryptographic hash chaining on `audit_events` using SHA-256 and sequential pointers.
  - `AuditChainVerifier` detects modified payloads, altered timestamps, or reordered records.
  - Periodic integrity checks flag discrepancies immediately (`CHAIN_BROKEN`).

### R — Repudiation
- **Threat**: Responder denies receiving an assignment or dispatcher claims an incident was closed when it was not.
- **Mitigations**:
  - Every state transition in `incident_service` generates an immutable `INCIDENT_STATE_TRANSITION` audit record with `previous_state`, `new_state`, actor ID, and role.
  - Responder assignments generate `INCIDENT_ASSIGNMENT` audit records.

### I — Information Disclosure
- **Threat**: Unauthorized user or compromised account reads tourist GPS trails or private medical info.
- **Mitigations**:
  - Role-Based Access Control (`require_roles([UserRole.ADMIN, UserRole.AUTHORITY])`).
  - Strict PII isolation: GPS history and tourist names are never logged into audit payload fields.
  - Location read events (`LOCATION_HISTORY_READ`, `LOCATION_ACTIVE_SNAPSHOT_READ`) are actively audited.

### D — Denial of Service
- **Threat**: Flooding API or offline sync endpoint to exhaust backend resources and prevent SOS delivery.
- **Mitigations**:
  - Fast-path SOS emergency handling completely isolated from non-critical logging.
  - Idempotency keys (`IdempotencyRecord`) prevent duplicate replay attacks during offline sync.
  - Fail-safe audit design: Audit hash calculations run in-memory with sub-millisecond overhead.

### E — Elevation of Privilege
- **Threat**: Tourist attempts to access admin audit verification or CCTV investigation endpoints.
- **Mitigations**:
  - FastAPI dependency injection enforcement (`get_current_active_user`, `require_roles`).
  - Audit access strictly restricted to `ADMIN` and `AUTHORITY` roles.
  - Unauthorized permission change attempts trigger security audit warnings.

---

## 4. Residual Risks & Accepted Constraints

1. **Physical Database Host Seizure**: A full database host compromise allows root deletion of the entire table; mitigated by offsite read-only replica replication and periodic external checkpoint anchoring.
2. **Device-Level Offline Clock Skew**: Handled by monotonic sequence numbers and server-side receipt timestamps during batch sync.
