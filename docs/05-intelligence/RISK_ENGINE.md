# KIROSHI Intelligent Risk Engine (v0.3)

## 1. Overview & Architectural Philosophy

The **KIROSHI Intelligent Risk Engine** serves as the primary situational awareness and heuristic evaluation component of the platform. It continuously processes real-time GPS telemetry, geofence boundary events, and itinerary path contexts to evaluate tourist vulnerability and risk.

```
GPS Receiver (Mobile)
        │
        ▼
Location Ingestion (/api/v1/location)
        │
        ▼
PostGIS Geospatial Processing (Spatial Containment & Boundary Crossings)
        │
        ▼
Location Broadcast (WebSocket -> Authority Dashboards)
        │
        ▼
Risk Signal Extraction & Cross-Track Geodesic Math
        │
        ▼
Deterministic Risk Evaluator (Rule Engine v0.3)
        │
        ▼
Multi-Factor Data Confidence & Natural Language Explainability
        │
        ▼
RiskAssessment Persistence (PostgreSQL / PostGIS)
        │
        ▼
Risk Update Broadcast (WebSocket -> Subscribed Dispatch Consoles)
```

### Core Tenet: Human-in-the-Loop Verification
The Risk Engine identifies anomalous conditions and flags elevated concern. **It NEVER automatically declares an emergency, dispatches responders, or replaces human judgment.** A high risk score indicates that conditions warrant operator attention, not that the tourist is confirmed in danger.

---

## 2. Signal Architecture

Risk evaluation is decomposed into modular, independently testable signal extractors. Each signal produces a normalized score $s_i \in [0.0, 1.0]$, weighted by its domain importance $w_i$.

| Signal Type | Description | Weight ($w_i$) | Raw Unit | Config Thresholds |
| :--- | :--- | :---: | :---: | :--- |
| `ROUTE_DEVIATION` | Geodesic cross-track distance to closest segment of planned itinerary polyline. | 0.35 | Meters | $\le 100\text{m}$: Safe (0.0)<br>$\le 300\text{m}$: Minor (0.0–0.4)<br>$\le 800\text{m}$: Moderate (0.4–0.85)<br>$> 800\text{m}$: Severe (0.85–1.0) |
| `HIGH_RISK_ZONE` | Containment within natural hazard polygons (landslides, avalanche paths, flash floods). | 0.45 | Boolean | Inside = 1.0; Outside = 0.0 |
| `RESTRICTED_ZONE` | Containment within legal curfews, military sectors, or closed national parks. | 0.25 | Boolean | Inside = 1.0; Outside = 0.0 |
| `PROLONGED_INACTIVITY`| Immobility within a 15m radius over consecutive historical location pings. | 0.25 | Minutes | $< 15\text{m}$: Safe (0.0)<br>$15–30\text{m}$: Rest stop (0.0–0.3)<br>$30–60\text{m}$: Prolonged (0.3–0.8)<br>$> 60\text{m}$: Severe (0.8–1.0) |
| `UNUSUAL_SPEED` | Uncharacteristic velocity exceeding transport modality tolerances. | 0.15 | m/s | $> 38.0\text{ m/s}$ (~137 km/h): 1.0 |
| `ZONE_EVENT` | Recent geofence state-transition events logged within the current ingestion cycle. | 0.15 | Categorical | ENTER high-risk: 0.8<br>ENTER restricted: 0.5 |

---

## 3. Mathematical Scoring Formula & Normalization

The composite risk score $R$ is calculated deterministically:

$$R_{\text{raw}} = \sum_{i=1}^{N} \left( s_i \times w_i \right)$$

$$R = \min\left(1.0, \max\left(0.0, R_{\text{raw}}\right)\right)$$

Where:
- $s_i$ is the normalized signal score ($0.0 \le s_i \le 1.0$)
- $w_i$ is the configured signal weight
- $R \in [0.0, 1.0]$ is strictly bounded and normalized.

The evaluation is **100% deterministic**: identical inputs under identical configuration and model version produce the exact same numerical score, category, and explanation.

---

## 4. Risk Levels & Centralized Thresholds

Risk thresholds are centralized in `RiskConfig` to eliminate magic numbers across the codebase:

```python
THRESHOLD_SAFE_MAX = 0.20     # [0.00, 0.20) -> SAFE
THRESHOLD_LOW_MAX = 0.40      # [0.20, 0.40) -> LOW
THRESHOLD_MEDIUM_MAX = 0.65   # [0.40, 0.65) -> MEDIUM
THRESHOLD_HIGH_MAX = 0.85     # [0.65, 0.85) -> HIGH
# [0.85, 1.00] -> CRITICAL
```

| Level | Score Range | Operational Meaning | System Recommendation |
| :--- | :---: | :--- | :--- |
| **SAFE** | $0.00 \le R < 0.20$ | Nominal telemetry, on itinerary, clear of hazard zones. | `MONITOR` |
| **LOW** | $0.20 \le R < 0.40$ | Minor off-trail movement or brief extended rest stop. | `MONITOR` |
| **MEDIUM** | $0.40 \le R < 0.65$ | Noticeable route deviation or entry into restricted perimeter. | `REVIEW` |
| **HIGH** | $0.65 \le R < 0.85$ | Concurrent hazard zone entry, severe deviation, or immobility. | `CONTACT_TOURIST` |
| **CRITICAL** | $0.85 \le R \le 1.00$ | Compound crisis indicators (e.g. hazard zone + deep deviation + immobility). | `ESCALATE_FOR_HUMAN_REVIEW` |

---

## 5. Confidence Calculation

Confidence in KIROSHI reflects the **quality, completeness, and freshness of observational data**, rather than a duplicate of risk.

Confidence $C \in [0.10, 1.00]$ is computed as:

$$C = 0.30 \cdot F_{\text{freshness}} + 0.30 \cdot F_{\text{accuracy}} + 0.20 \cdot F_{\text{history}} + 0.20 \cdot F_{\text{route}}$$

Where:
- **$F_{\text{freshness}}$**: `LIVE` ($\le 30\text{s}$) = 1.0; `RECENT` ($\le 3\text{m}$) = 0.65; `STALE` ($> 3\text{m}$) = 0.20.
- **$F_{\text{accuracy}}$**: Good ($\le 10\text{m}$) = 1.0; Moderate ($\le 30\text{m}$) = 0.70; Marginal ($\le 75\text{m}$) = 0.40; Degraded ($> 75\text{m}$) = 0.15.
- **$F_{\text{history}}$**: Trajectory depth ($\ge 10$ points = 1.0; scaling linearly down to 0.1 for 0 points).
- **$F_{\text{route}}$**: Itinerary available = 1.0; No planned route waypoints = 0.30.

---

## 6. Explainability & Human Verification

Every persisted `RiskAssessment` records human-understandable audit text generated by `RiskExplainer`:
- Identifies specific contributing hazards (e.g. `"Active location inside a high-risk safety perimeter"`, `"Moderate deviation from planned trail (440m off path)"`).
- Synthesizes multiple overlapping factors into coherent operational sentences.
- Avoids opaque black-box classifications.

---

## 7. Model Versioning

All persisted evaluations record `model_version: "v0.3-rule-engine"`.
This guarantees auditability: historical records maintain their context even if future milestones introduce statistical models or altered weights.

---

## 8. Limitations & False Positives/Negatives

1. **GPS Canyon & Multipath Drift**: In dense urban or mountainous topography, GPS drift may artificially register as route deviation. The 100m tolerance buffer and accuracy-weighted confidence mitigate this.
2. **Intentional Detours**: Tourists may intentionally visit scenic overlooks or shops. The system treats moderate deviation as `LOW`/`MEDIUM` review, never as an emergency.
3. **Legitimate Rest Stops**: Dining or resting at viewpoints may trigger prolonged inactivity warnings after 30 minutes. Operators must verify context before taking action.
4. **Vehicular Transit**: Normal highway speeds may trigger unusual speed signals if the trip modality is assumed to be pedestrian.
