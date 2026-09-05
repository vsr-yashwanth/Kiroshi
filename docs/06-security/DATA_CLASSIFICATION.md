# KIROSHI Data Classification Policy (v0.7)

## 1. Classification Framework

KIROSHI classifies all system data into four explicit tiers based on privacy risk, confidentiality, regulatory impact (GDPR / DPDP), and operational sensitivity.

```
+-------------------------------------------------------------------------+
|                              HIGHLY SENSITIVE                           |
|  Passwords, Private Keys, JWT Secrets, Government IDs, Live SOS Audio    |
+-------------------------------------------------------------------------+
|                                 SENSITIVE                               |
|  GPS Coordinates, Medical Info, Phone Numbers, CCTV Facial Feeds        |
+-------------------------------------------------------------------------+
|                                 INTERNAL                                |
|  Risk Scores, Anonymized Incident IDs, Audit Hashes, System Metadata    |
+-------------------------------------------------------------------------+
|                                  PUBLIC                                 |
|  Geofence Boundaries, Public Safety Zones, High-Level Aggregate Alerts  |
+-------------------------------------------------------------------------+
```

---

## 2. Field-by-Field Classification Matrix

| Data Entity | Specific Fields | Classification | Storage Location | Access Controls (RBAC) | Retention Period | External Anchoring Allowed? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Authentication Secrets** | Password hashes, JWT secrets, salt | `HIGHLY_SENSITIVE` | PostgreSQL (`users.hashed_password`), Env vars | System internal only. Zero API exposure. | Account lifetime | ❌ **STRICTLY NEVER** |
| **Tourist Identity** | Full name, Passport / Govt ID, Address | `HIGHLY_SENSITIVE` | PostgreSQL (`tourist_profiles`), encrypted at rest | Tourist (self), Authority (authorized search), Admin | Account lifetime + 30 days post-deletion | ❌ **STRICTLY NEVER** |
| **Emergency Contacts** | Contact name, phone number, relationship | `SENSITIVE` | PostgreSQL (`emergency_contacts`) | Tourist (self), Responders during active SOS | Account lifetime | ❌ **STRICTLY NEVER** |
| **GPS / Location History** | Latitude, Longitude, Altitude, Accuracy, Timestamp | `SENSITIVE` | PostgreSQL / PostGIS (`locations`) | Tourist (self), Responders (active incident), Authority | 90 days rolling (anonymized after) | ❌ **STRICTLY NEVER** |
| **Trip & Itineraries** | Trip name, dates, planned stops, itinerary items | `INTERNAL` | PostgreSQL (`trips`, `itineraries`) | Tourist (self), Emergency responders | 1 year | ❌ **STRICTLY NEVER** |
| **Incident Details** | Type, Severity, Status, Description, Location | `SENSITIVE` | PostgreSQL (`incidents`) | Tourist (creator), Responders, Authority, Admin | 7 years (legal / emergency audit) | ❌ **STRICTLY NEVER** (Raw details) |
| **Incident State Transitions** | `from_status`, `to_status`, `reason`, timestamps | `INTERNAL` | PostgreSQL (`incident_state_history`, `audit_events`) | Authority, Responders, Admin, Auditor | 7 years | ⚠️ Commitments / Hashes Only |
| **Risk Evaluations** | Deterministic score, sub-scores, contributing factors | `INTERNAL` | PostgreSQL (`risk_assessments`) | Tourist (self), Authority, Admin | 90 days | ❌ **STRICTLY NEVER** |
| **CCTV Feeds & Raw Imagery** | Video frames, CCTV RTSP stream URLs | `HIGHLY_SENSITIVE` | Dedicated camera storage / edge buffer | Authority only with active investigation order | 30 days | ❌ **STRICTLY NEVER** |
| **CV Detection Metadata** | Fall confidence, crowd density, bounding box coords | `INTERNAL` | PostgreSQL (`cctv_investigations`) | Authority, Responders | 180 days | ❌ **STRICTLY NEVER** |
| **Audit Event Records** | Event type, sequence #, actor ID/role, timestamps | `INTERNAL` | PostgreSQL (`audit_events`) | Admin, Auditor (read-only), Authority (export) | 7 years (tamper-evident hash chain) | ⚠️ Commitments / Hashes Only |
| **Audit Cryptographic Hashes**| `previous_hash`, `event_hash`, Merkle roots | `INTERNAL` / `PUBLIC` | PostgreSQL (`audit_events`), Trust Anchors | Publicly verifiable, Auditor, Admin | Permanent | ✅ **PERMITTED (Hashes/Roots Only)** |
| **Geofences & Hazard Zones** | Zone polygon, risk category, advisory title | `PUBLIC` | PostgreSQL / PostGIS (`geo_zones`) | All authenticated & anonymous users | Indefinite / active lifecycle | ✅ **PERMITTED** |

---

## 3. Strict Rules for External Anchoring & Public Trust

1. **Zero PII on External Anchors**: Under no circumstances shall personally identifiable information (names, emails, phone numbers, passport numbers, GPS points, raw CCTV imagery, or incident descriptions) be exported to external timestamping services or blockchains.
2. **Hash-Only Export**: Only fixed-size cryptographic digests (`SHA-256` checksums, Merkle roots, sequence numbers, and checkpoint timestamps) may be published or anchored externally.
3. **Anonymized Audit Trails**: When users exercise their "Right to be Forgotten" (GDPR Art. 17), `actor_id` references in `audit_events` are set to `NULL` while retaining denormalized `actor_role` to preserve cryptographic chain continuity without violating privacy rights.
