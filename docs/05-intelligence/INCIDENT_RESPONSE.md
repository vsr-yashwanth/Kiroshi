# Incident Management & Emergency Response (v0.4)

## 1. Domain Architecture

The **Incident** domain is completely independent of the Risk Engine. While the Risk Engine can emit an incident signal when risk thresholds are exceeded, the Incident domain authoritatively owns:
- Operational incident status
- Chronological append-only timeline events (`IncidentEvent`)
- Responder assignments and reassignment history (`IncidentAssignment`)
- Authoritative state machine transitions and access control

---

## 2. Server-Enforced State Machine

The Incident lifecycle is governed by a strict, authoritative server-side state machine with 9 discrete states. States cannot be freely edited as arbitrary strings.

```mermaid
stateDiagram-v2
    [*] --> DETECTED: SOS / Risk Engine / Authority / System
    
    DETECTED --> VERIFYING: Authority starts triage
    DETECTED --> DISMISSED: Authority / Admin
    
    VERIFYING --> VERIFIED: Authority confirms distress
    VERIFYING --> DISMISSED: Authority / Admin
    
    VERIFIED --> ESCALATED: Authority escalates
    VERIFIED --> ASSIGNED: Authority assigns responder
    VERIFIED --> DISMISSED: Authority / Admin
    
    ESCALATED --> ASSIGNED: Authority assigns responder
    
    ASSIGNED --> RESPONDING: Responder begins field response
    ASSIGNED --> ASSIGNED: Authority reassigns responder
    
    RESPONDING --> RESOLVED: Responder resolves distress
    
    RESOLVED --> CLOSED: Authority closes & signs off
    
    CLOSED --> [*]: Terminal State
    DISMISSED --> [*]: Terminal State
```

### Transition & Role Authorization Matrix

| From State | Allowed Target State | Authorized Roles | Operational Meaning |
| :--- | :--- | :--- | :--- |
| `DETECTED` | `VERIFYING` | `AUTHORITY`, `ADMIN` | Dispatcher initiates verification protocol |
| `DETECTED` | `DISMISSED` | `AUTHORITY`, `ADMIN` | False alarm or invalid trigger |
| `VERIFYING` | `VERIFIED` | `AUTHORITY`, `ADMIN` | Incident confirmed genuine |
| `VERIFYING` | `DISMISSED` | `AUTHORITY`, `ADMIN` | False alarm confirmed |
| `VERIFIED` | `ESCALATED` | `AUTHORITY`, `ADMIN` | High-urgency operational escalation |
| `VERIFIED` | `ASSIGNED` | `AUTHORITY`, `ADMIN` | Direct responder dispatch |
| `VERIFIED` | `DISMISSED` | `AUTHORITY`, `ADMIN` | Cancellation before dispatch |
| `ESCALATED` | `ASSIGNED` | `AUTHORITY`, `ADMIN` | Responder dispatch for escalated case |
| `ASSIGNED` | `RESPONDING` | `RESPONDER`, `ADMIN` | Assigned officer is en route / on site |
| `ASSIGNED` | `ASSIGNED` | `AUTHORITY`, `ADMIN` | Reassignment to closer responder |
| `RESPONDING` | `RESOLVED` | `RESPONDER`, `ADMIN` | Officer has aided tourist / eliminated hazard |
| `RESOLVED` | `CLOSED` | `AUTHORITY`, `ADMIN` | Final administrative sign-off |

### Terminal States
- `CLOSED` and `DISMISSED` are strictly terminal. Any attempt to transition out of these states returns HTTP 400 (`InvalidStateTransitionError`).

---

## 3. Authority & Responder Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Tourist as Traveler
    actor Authority as Dispatch Authority
    actor Responder as Field Responder
    participant System as Incident Service

    Tourist->>System: Distress Beacon Triggered (Status: DETECTED)
    System->>Authority: Real-Time WebSocket (INCIDENT_CREATED)
    Authority->>System: Transition -> VERIFYING (Triage commenced)
    Authority->>System: Transition -> VERIFIED (Distress validated)
    Authority->>System: Transition -> ESCALATED
    Authority->>System: Assign Responder (Status -> ASSIGNED)
    System->>Responder: In-App Notification (NEW EMERGENCY ASSIGNMENT)
    Responder->>System: Transition -> RESPONDING (En route)
    System->>Authority: Real-Time WebSocket (INCIDENT_STATUS_CHANGED)
    Responder->>System: Transition -> RESOLVED (Evacuated / Safe)
    System->>Authority: Real-Time WebSocket (INCIDENT_STATUS_CHANGED)
    Authority->>System: Transition -> CLOSED (Debrief complete)
```

---

## 4. Notification Architecture & Fault Isolation

```mermaid
flowchart TD
    A[Incident Action / SOS] --> B[Incident Database Commit]
    B --> C{Notification Dispatch}
    C -->|Channel: IN_APP| D[InAppNotificationProvider]
    C -.->|Future: PUSH| E[PushProvider]
    C -.->|Future: SMS| F[SmsProvider]
    D -->|Persisted in DB| G[(notifications table)]
    
    subgraph Fault Isolation Guarantee
    C -->|Network / Provider Error| H[Log Warning & Continue]
    H --> I[Incident Remains Committed & Active]
    end
```

### Critical Reliability Rules
1. **Zero Rollback on Notification Failure**:
   If notification delivery fails or throws an exception, the incident creation and state transitions **MUST NEVER BE ROLLED BACK**. Incident persistence is mission-critical; notifications are delivery layers.
2. **Notification Idempotency**:
   Notifications utilize idempotency keys to prevent duplicate notifications during retries.
3. **Pluggable Architecture**:
   The `BaseNotificationProvider` interface provides an abstraction for future SMS, Push, and Email providers without changing incident business logic.
