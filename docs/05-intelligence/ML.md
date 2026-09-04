# Machine Learning Strategy & Evolution

## Current State: Milestone v0.3

> [!IMPORTANT]
> **KIROSHI v0.3 does NOT employ neural networks or black-box machine learning models.**
> The current intelligent risk engine is a **deterministic, transparent, rule-based expert scoring system** (`v0.3-rule-engine`).

### Why Deterministic Scoring in v0.3?
1. **Explainability & Trust**: Safety and authority dispatch systems require immediate, transparent justification for every escalated state. An operator cannot rely on uninterpretable neural logits when evaluating tourist safety.
2. **Reproducibility**: Identical telemetry data under identical configuration produces identical outcomes.
3. **Auditability**: Legal and safety audits require an unambiguous trail from raw sensor input to system recommendation.
4. **Zero Cold-Start / Training Bias**: Deep models require massive annotated real-world emergency datasets which do not exist during initial platform rollout.

---

## Future State: Planned ML Enhancements (v0.5+)

Future milestones may selectively incorporate machine learning as **advisory assistance** layers rather than autonomous controllers:

### 1. Modality Classification
- **Approach**: Random Forest or lightweight 1D-CNN on accelerometer/gyroscope time series and GPS velocity profiles.
- **Purpose**: Automatically distinguish pedestrian hiking, bicycling, train travel, and automotive transport to dynamically adjust velocity thresholds and route buffers.

### 2. Anomaly Detection for Trajectory Drift
- **Approach**: Isolation Forests or Gaussian Mixture Models (GMM) trained on aggregate historical tourist paths.
- **Purpose**: Identify subtle deviations from typical tourist movement patterns without requiring explicit pre-configured itinerary polylines.

### 3. Terrain Difficulty & Weather Hazard Forecasting
- **Approach**: Spatial gradient boosting on elevation models (DEM) combined with meteorological precipitation radar.
- **Purpose**: Preemptively increase environmental risk weights before tourists enter deteriorating weather conditions.

### 4. Human-in-the-Loop Active Learning
- **Approach**: Operator feedback (dismissed false alarms, confirmed incidents) captured as structured feedback to calibrate heuristic weights.
