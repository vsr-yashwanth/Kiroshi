# Computer Vision Datasets & Manifest Documentation (v0.6)

## Approved Datasets

### 1. Multiple Cameras Fall Dataset
- **Kaggle URL**: `https://www.kaggle.com/datasets/soumicksarker/multiple-cameras-fall-dataset`
- **Purpose**: Primary video-based multi-camera fall detection and benchmark evaluation.
- **Type**: Real-world recorded video dataset.
- **Classes**: `fall`, `adl_normal_activity`.
- **Format**: MP4 video streams across synchronized camera viewpoints.
- **Status**: Scaffolding and manifest pipeline verified.

---

### 2. CCTV Incident Dataset: Fall & Lying Down Detection
- **Kaggle URL**: `https://www.kaggle.com/datasets/simuletic/cctv-incident-dataset-fall-and-lying-down-detection`
- **Purpose**: Keypoint and posture development for synthetic outdoor CCTV simulation.
- **Type**: **SYNTHETIC** (3D rendered human avatar simulations).
- **Classes**: `fall`, `lying_down`, `walking`, `standing`.
- **Status**: Scaffolding and synthetic labeling pipeline verified.

---

### 3. Fall Video Dataset
- **Kaggle URL**: `https://www.kaggle.com/datasets/payutch/fall-video-dataset`
- **Purpose**: Secondary validation and cross-dataset testing.
- **Type**: Real-world recorded video.
- **Classes**: `fall`, `non_fall`.
- **Status**: Benchmark manifest pipeline verified.

---

## Leakage-Safe Splitting Protocol
- Splitting is performed strictly at the **video/subject** level using `generate_leakage_safe_splits()` in `ml/pipelines/dataset_pipeline.py`.
- Frames or keypoints from the same video are never partitioned across training and testing sets.
