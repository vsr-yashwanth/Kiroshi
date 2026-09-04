# Machine Learning Models & Pipelines

> Status: PLANNED (v0.3 Risk Engine & v0.6 Computer Vision Targets)

Per the KIROSHI Engineering Standards (`docs/02-architecture/ARCHITECTURE.md`), ML components are modularized here and strictly decoupled from the core API controllers:
- `models/`: Exported model weights and architecture definitions (e.g., MediaPipe Pose, Anomaly Scorer).
- `pipelines/`: Data ingestion, preprocessing, and feature engineering pipelines.
- `evaluation/`: Ground-truth benchmark evaluation scripts tracking precision, recall, F1, and latency.
- `tests/`: Isolated model unit tests and validation checks.

In milestone v0.1.0, these directories remain cleanly scaffolded without premature implementation.
