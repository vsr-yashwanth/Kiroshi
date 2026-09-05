# Privacy Policy & Data Governance — KIROSHI

> Status: UPDATED (v0.7 Advanced Audit & Trust)

---

## 1. Privacy-by-Design Principles

1. **Explicit Consent**: Profile records include an affirmative `consent_given` flag. Tourists must grant permission for safety monitoring.
2. **Data Minimization**: Only essential information (emergency contacts, critical medical notes) is captured.
3. **Role-Based Segregation**: Tourist medical and contact details are visible only to the tourist and authorized emergency personnel/authorities.
4. **No Public Identification**: Unanonymized passport or government ID details are hashed or restricted from external exposure.
5. **Absolute Prohibition of PII on External Anchors / Ledgers**:
   - Under no circumstances shall tourist names, phone numbers, passport numbers, raw GPS trajectories, medical notes, or raw CCTV frames be written to external registries or blockchains.
   - Only non-sensitive cryptographic digests (`SHA-256` checksums, Merkle roots, sequence numbers, timestamps) may be anchored externally.
6. **Right to Erasure (GDPR Art. 17 / DPDP) Compliance**:
   - When a tourist requests account deletion, their `tourist_profiles`, `emergency_contacts`, and location histories are deleted.
   - In `audit_events`, the foreign key `actor_id` is set to `NULL` (`ON DELETE SET NULL`), preserving the mathematical continuity of the cryptographic audit hash chain while completely removing the user's personally identifiable association.
7. **Access-Auditing for Sensitive Data**:
   - Every read of location history, active snapshot, and CCTV investigation feed is recorded as an immutable audit event (`LOCATION_HISTORY_READ`, `CCTV_INVESTIGATION_COMPLETED`).
