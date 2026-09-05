"""
Dataset Acquisition, Validation, and Leakage-Safe Splitting Pipeline for KIROSHI v0.6.

Approved Datasets:
1. Multiple Cameras Fall Dataset (Kaggle: soumicksarker/multiple-cameras-fall-dataset)
2. CCTV Incident Dataset: Fall & Lying Down Detection (Kaggle: simuletic/cctv-incident-dataset-fall-and-lying-down-detection) - Synthetic
3. Fall Video Dataset (Kaggle: payutch/fall-video-dataset)
"""

from __future__ import annotations

import os
import json
import random
from typing import Dict, List, Any, Optional
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
SPLITS_DIR = BASE_DIR / "data" / "splits"

APPROVED_DATASETS = {
    "multiple_cameras_fall": {
        "kaggle_slug": "soumicksarker/multiple-cameras-fall-dataset",
        "type": "video_real",
        "description": "Primary video-based multi-camera fall detection dataset.",
        "synthetic": False,
        "classes": ["fall", "adl_normal_activity"],
    },
    "cctv_incident_dataset": {
        "kaggle_slug": "simuletic/cctv-incident-dataset-fall-and-lying-down-detection",
        "type": "cctv_synthetic",
        "description": "Synthetic 3D rendered CCTV scene dataset for fall and lying down posture development.",
        "synthetic": True,
        "classes": ["fall", "lying_down", "walking", "standing"],
    },
    "fall_video_dataset": {
        "kaggle_slug": "payutch/fall-video-dataset",
        "type": "video_real",
        "description": "Real-world validation videos of falling and non-falling actions.",
        "synthetic": False,
        "classes": ["fall", "non_fall"],
    }
}


def initialize_data_directories() -> None:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    SPLITS_DIR.mkdir(parents=True, exist_ok=True)


def generate_leakage_safe_splits(
    items: List[Dict[str, Any]],
    group_key: str = "video_id",
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Splits dataset at the video/subject level to prevent data leakage across frames.
    """
    random.seed(seed)
    
    # Group items by group_key (e.g., video_id or subject_id)
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
        gid = str(item.get(group_key, "unknown"))
        groups.setdefault(gid, []).append(item)

    group_keys = list(groups.keys())
    random.shuffle(group_keys)

    n_groups = len(group_keys)
    n_train = int(n_groups * train_ratio)
    n_val = int(n_groups * val_ratio)

    train_groups = set(group_keys[:n_train])
    val_groups = set(group_keys[n_train:n_train + n_val])
    test_groups = set(group_keys[n_train + n_val:])

    splits: Dict[str, List[Dict[str, Any]]] = {
        "train": [],
        "val": [],
        "test": []
    }

    for item in items:
        gid = str(item.get(group_key, "unknown"))
        if gid in train_groups:
            splits["train"].append(item)
        elif gid in val_groups:
            splits["val"].append(item)
        else:
            splits["test"].append(item)

    return splits


def create_reproducible_manifest(splits: Dict[str, List[Dict[str, Any]]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(splits, f, indent=2)
