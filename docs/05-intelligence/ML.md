# Machine Learning Architecture & Failure Isolation (v0.6)

## Decoupled Architecture
The Computer Vision / ML system is strictly decoupled from the core KIROSHI backend:

- **Interface Abstraction**: `ml.interfaces.BaseModel`, `ml.interfaces.DetectionResult`
- **Model Engine**: `ml.models.fall_detector.FallDetector`
- **Evaluation**: `ml.evaluation.evaluate.py`
- **Pipelines**: `ml.pipelines.dataset_pipeline.py`

---

## Failure Isolation & Resilience Guarantees

| Failure Mode | System Response | Core Safety Impact |
| :--- | :--- | :--- |
| **ML Engine Timeout** | Bounded execution aborts after timeout threshold | Incident creation & SOS dispatch proceed unaffected |
| **Corrupted Frame / Pose Data** | FallDetector returns `DetectionType.NORMAL_POSTURE` or `UNKNOWN` | No crashes; logged to error stream |
| **Camera Feed Unavailable** | Returns `InvestigationStatus.NO_FOOTAGE_AVAILABLE` | Incident response continues normally |
| **ML Package Missing** | Graceful fallback in risk evaluator | Risk engine evaluates GPS/geozone signals without ML |
