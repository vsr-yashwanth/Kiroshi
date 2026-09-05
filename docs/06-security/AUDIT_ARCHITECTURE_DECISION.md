# KIROSHI Audit Architecture & Trust Decision Matrix (v0.7)

## 1. Executive Summary

In accordance with KIROSHI v0.7 specifications, we conducted a rigorous architectural evaluation of audit logging and trust verification approaches. The objective is to ensure non-repudiation, tamper evidence, and operational reliability for emergency management without compromising tourist privacy, system latency, or availability.

---

## 2. Four-Option Comparison Matrix

| Evaluation Dimension | Option A: Traditional Append-Only Log | Option B: Cryptographic Hash Chain | Option C: External Tamper-Evident Registry | Option D: Blockchain Anchoring |
| :--- | :--- | :--- | :--- | :--- |
| **Tamper Resistance** | Low (DB admin can rewrite rows silently) | **High (Any modification breaks SHA-256 chain)** | Very High (External multi-party verification) | Very High (Decentralized consensus) |
| **Detection of Row Deletion / Reordering** | None | **Immediate (Breaks previous_hash & seq #)** | Immediate (Root hash mismatch) | Immediate (Block header mismatch) |
| **Implementation Complexity** | Minimal | **Low / Moderate (Clean Python engine)** | High (External API integration & auth) | Extremely High (Smart contracts, node sync, gas management) |
| **Operational & Maintenance Cost** | $0 extra | **$0 extra (Embedded in core DB)** | Low to Moderate (SaaS registry pricing) | High (Transaction fees, gas tokens, RPC nodes) |
| **Write Latency / Performance Impact** | < 1 ms | **< 2 ms (SHA-256 calculation overhead)** | 100 - 500 ms (Network I/O) | 2,000 - 15,000 ms (Block confirmation) |
| **System Availability Dependency** | Local DB only | **Local DB only (Zero external deps)** | Depends on external vendor uptime | Depends on blockchain RPC / gas liquidity |
| **Privacy / GDPR Compliance** | High | **High (Payloads contain IDs & metadata only)** | Moderate (Requires rigorous hash-only gating) | Low / Risk of accidental PII immutability |
| **Emergency Path Resilience (SOS)** | Never blocks | **Never blocks (In-memory hash calculation)** | Risk of blocking if synchronous | Critical hazard if blocking SOS dispatch |
| **Suitability for KIROSHI v0.7** | Insufficient for Trust | ⭐ **OPTIMAL & SELECTED** | Optional Future Extension | ❌ **REJECTED (Unjustified Complexity)** |

---

## 3. Decision Framework & Threat Model Evaluation

### 1. Who is the attacker?
- Internal rogue operators, compromised administrator credentials, or malicious actors with read/write access attempting to alter incident timelines, dismissals, or SOS response histories.

### 2. Does an external blockchain solve a real problem for KIROSHI?
- **No.** The primary requirement is detecting unauthorized alterations to incident histories, SOS dispatches, and privilege escalations. A local SHA-256 cryptographic hash chain provides mathematical tamper evidence with zero latency penalty and zero external dependency risk.

### 3. What happens if an external trust network goes down?
- In an emergency rescue system (KIROSHI), life safety is paramount. An SOS creation, risk calculation, or responder dispatch must **NEVER** fail or stall because of network timeouts, gas spikes, or blockchain node unresponsiveness.

### 4. What are the privacy implications of blockchain?
- Blockchains are permanently immutable. If PII (names, phone numbers, GPS coordinates) or sensitive medical/SOS details are ever inadvertently posted to a public blockchain, they cannot be deleted, directly violating GDPR Art. 17 ("Right to be Forgotten") and Indian DPDP legislation.

---

## 4. Final Architectural Decision

### **Selected Architecture: Option B (Cryptographic Hash Chain) with Isolated Trust Anchor Adapter**

1. **Core Hash Chain Engine**:
   - Every security-sensitive action (`AUTH`, `PROFILE`, `LOCATION_READ`, `INCIDENT`, `EXPORT`, `ASSIGNMENT`, `CCTV`) generates an `AuditEvent`.
   - Each event contains a strict sequence number, canonical metadata, and a SHA-256 digest linked to the `previous_hash`.
   - Genesis is anchored at `0000000000000000000000000000000000000000000000000000000000000000`.

2. **Tamper Detection**:
   - Automated sequential verification checks detect any inserted, deleted, reordered, or modified records with exact sequence identification (`CHAIN_BROKEN` at sequence `#N`).

3. **Modular Trust Anchor Interface (`BaseTrustAnchor`)**:
   - Provides an abstracted adapter layer (`LocalTrustAnchor`, `SimulatedExternalRegistryAnchor`) allowing optional periodic checkpoint anchoring without coupling core business logic to external networks.

4. **Blockchain Status for v0.7**:
   - **REJECTED FOR CORE PLATFORM**: Direct blockchain dependency is rejected for v0.7 because it adds high operational fragility, cost, and privacy risks without providing additional safety to tourists or emergency responders.
