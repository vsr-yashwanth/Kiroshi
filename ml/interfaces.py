from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# Centralized Model Versioning Constants
DEFAULT_MODEL_NAME = "kiroshi-fall-detector"
DEFAULT_MODEL_VERSION = "0.6.0"
DEFAULT_PIPELINE_VERSION = "0.6.0"


class DetectionType(str, enum.Enum):
    NORMAL_POSTURE = "NORMAL_POSTURE"
    POSSIBLE_FALL = "POSSIBLE_FALL"
    LYING_DOWN = "LYING_DOWN"
    RAPID_DESCENT = "RAPID_DESCENT"
    UNKNOWN = "UNKNOWN"


class DetectionSignal(BaseModel):
    name: str = Field(..., description="Name of the computed signal (e.g., 'vertical_velocity', 'aspect_ratio')")
    value: float = Field(..., description="Calculated numerical value for this signal")
    threshold: float = Field(..., description="Decision threshold applied")
    triggered: bool = Field(..., description="Whether this individual signal contributed to the detection")
    description: str = Field(..., description="Explainable description of the signal condition")


class Keypoint(BaseModel):
    x: float
    y: float
    z: Optional[float] = 0.0
    visibility: Optional[float] = 1.0


class PoseFrame(BaseModel):
    frame_index: int
    timestamp_offset_ms: float
    bounding_box: Optional[List[float]] = None  # [x_min, y_min, x_max, y_max] normalized 0-1
    keypoints: Dict[str, Keypoint] = Field(default_factory=dict)


class DetectionResult(BaseModel):
    detection_type: DetectionType
    confidence: float = Field(..., ge=0.0, le=1.0, description="Calibrated model confidence score")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_name: str = DEFAULT_MODEL_NAME
    model_version: str = DEFAULT_MODEL_VERSION
    pipeline_version: str = DEFAULT_PIPELINE_VERSION
    signals: List[DetectionSignal] = Field(default_factory=list)
    explanation: str = Field(..., description="Human-readable explainability summary")
    observation_window_ms: float = Field(default=0.0, description="Length of temporal analysis window in ms")
    frame_count_analyzed: int = Field(default=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)
