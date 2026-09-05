# KIROSHI Disaster Recovery & Operational Continuity (v0.7)

## 1. Scope & Objective

This document defines disaster recovery, backup procedures, audit chain restoration, and incident handling for KIROSHI v0.7. The core mission is to protect life safety during natural disasters, technical outages, and data corruption events.

---

## 2. Recovery Objectives

| Metric | Target | Current Measured Status |
| :--- | :--- | :--- |
| **RPO (Recovery Point Objective)** | < 5 minutes for active incidents / SOS | **NOT YET MEASURED** (Production benchmark pending) |
| **RTO (Recovery Time Objective)** | < 15 minutes for core dispatch service | **NOT YET MEASURED** (Production benchmark pending) |
| **Audit Log Integrity Target** | 100% verifiable SHA-256 chain continuity | **VERIFIED BY UNIT & E2E SUITE** |

---

## 3. Database & Audit Chain Backup Strategy

### Daily Full & Continuous WAL Archiving
- **PostgreSQL Base Backup**: Daily full pg_dump snapshot stored in encrypted off-site cloud storage.
- **WAL (Write-Ahead Logging)**: Continuous WAL streaming to enable Point-in-Time Recovery (PITR).

### Audit Chain Backup Isolation
- Audit events are backed up into a secondary append-only replica storage.
- Checkpoints of the latest `event_hash` and sequence number are exported periodically via `TrustAnchor`.

---

## 4. Audit Chain Recovery & Integrity Verification

In the event of database corruption or ungraceful failover:

1. **Restore PostgreSQL Database**:
   ```bash
   pg_restore -d kiroshi_db /backups/latest_snapshot.dump
   ```
2. **Execute Chain Verification Tool**:
   ```bash
   python -m backend.scripts.verify_audit_integrity
   # Calls AuditChainVerifier.verify_chain(all_events)
   ```
3. **Evaluate Verification Outcome**:
   - **`CHAIN_VALID`**: The database was restored with full cryptographic continuity.
   - **`CHAIN_BROKEN`**: Identifies exact sequence number `#N` and timestamp where data was truncated or altered. Administrators can inspect WAL logs to repair missing transactions.

---

## 5. Fail-Safe Emergency Protocols

### External Trust Layer Outage
- If external registries or network anchors are unavailable, the internal hash chain continues logging without disruption. Emergency SOS dispatch and incident handling **never block**.

### Offline Mobile Resilience
- In catastrophic field connectivity failures, tourist devices buffer location events and SOS triggers locally in encrypted Hive storage (`v0.5 Offline-First`), syncing automatically upon network restoration.
