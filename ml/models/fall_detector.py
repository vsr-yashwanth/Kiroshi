from __future__ import annotations

import math
import numpy as np
from typing import List, Optional, Tuple, Dict, Any
from ml.interfaces import (
    BaseModel,
    DetectionResult,
    DetectionSignal,
    DetectionType,
    Keypoint,
    PoseFrame,
    DEFAULT_MODEL_NAME,
    DEFAULT_MODEL_VERSION,
    DEFAULT_PIPELINE_VERSION,
)


class FallDetectorConfig(BaseModel):
    # Temporal & frame sampling parameters
    observation_window_ms: float = 2500.0
    min_frames_required: int = 3
    
    # Heuristic & Geometric thresholds
    aspect_ratio_fall_threshold: float = 0.95  # width / height > 0.95 indicates horizontal posture
    torso_angle_fall_threshold: float = 45.0  # Torso angle relative to horizontal < 45 degrees
    vertical_velocity_threshold: float = 0.25  # Normalized downward displacement per second
    ground_dwell_time_ms_threshold: float = 1000.0  # Prolonged rest after rapid motion
    
    # Confidence calibration weights
    weight_posture: float = 0.35
    weight_velocity: float = 0.40
    weight_ground_dwell: float = 0.25
    
    # Decision threshold for POSSIBLE_FALL
    fall_confidence_threshold: float = 0.65


class FallDetector:
    """
    Explainable Fall Detection Engine combining:
    1. Spatial Keypoint/Bounding-Box Posture Geometry (Aspect ratio, Torso Angle)
    2. Temporal Kinematic Analysis (Vertical descent velocity)
    3. Post-impact ground dwell time analysis
    
    CRITICAL SAFETY RULE:
    Outputs POSSIBLE_FALL, NEVER CONFIRMED_EMERGENCY.
    """

    def __init__(self, config: Optional[FallDetectorConfig] = None):
        self.config = config or FallDetectorConfig()

    def analyze_pose_sequence(self, sequence: List[PoseFrame]) -> DetectionResult:
        if not sequence:
            return DetectionResult(
                detection_type=DetectionType.UNKNOWN,
                confidence=0.0,
                explanation="No pose data or frames provided for analysis.",
                frame_count_analyzed=0,
            )

        if len(sequence) < self.config.min_frames_required:
            # Analyze single or sparse frame for static lying posture
            return self._analyze_static_posture(sequence[-1], len(sequence))

        # Sort chronologically by timestamp offset
        sorted_seq = sorted(sequence, key=lambda f: f.timestamp_offset_ms)
        start_ms = sorted_seq[0].timestamp_offset_ms
        end_ms = sorted_seq[-1].timestamp_offset_ms
        window_duration = max(1.0, end_ms - start_ms)

        signals: List[DetectionSignal] = []

        # 1. Posture & Aspect Ratio on final observed frames
        final_frame = sorted_seq[-1]
        aspect_ratio, torso_angle = self._calculate_posture_features(final_frame)
        
        is_horizontal = (aspect_ratio is not None and aspect_ratio > self.config.aspect_ratio_fall_threshold) or \
                         (torso_angle is not None and torso_angle < self.config.torso_angle_fall_threshold)

        posture_score = 0.0
        if is_horizontal:
            posture_score = min(1.0, (aspect_ratio or 1.0) / (self.config.aspect_ratio_fall_threshold * 1.5))
            signals.append(
                DetectionSignal(
                    name="horizontal_posture",
                    value=aspect_ratio if aspect_ratio is not None else (90.0 - (torso_angle or 0.0)),
                    threshold=self.config.aspect_ratio_fall_threshold,
                    triggered=True,
                    description=f"Subject is in horizontal posture (aspect ratio: {aspect_ratio:.2f} if available)",
                )
            )
        else:
            signals.append(
                DetectionSignal(
                    name="horizontal_posture",
                    value=aspect_ratio or 0.0,
                    threshold=self.config.aspect_ratio_fall_threshold,
                    triggered=False,
                    description="Subject remains in upright or standing posture",
                )
            )

        # 2. Vertical Kinematics (Downward velocity of hip / torso center)
        max_downward_velocity = self._calculate_max_downward_velocity(sorted_seq)
        velocity_triggered = max_downward_velocity > self.config.vertical_velocity_threshold
        velocity_score = min(1.0, max_downward_velocity / max(0.01, self.config.vertical_velocity_threshold * 1.5))

        signals.append(
            DetectionSignal(
                name="rapid_vertical_descent",
                value=max_downward_velocity,
                threshold=self.config.vertical_velocity_threshold,
                triggered=velocity_triggered,
                description=f"Observed peak downward displacement rate: {max_downward_velocity:.2f}/sec",
            )
        )

        # 3. Ground Dwell Time (Dwell in horizontal posture without recovery)
        dwell_ms = self._calculate_ground_dwell_time(sorted_seq)
        dwell_triggered = dwell_ms >= self.config.ground_dwell_time_ms_threshold
        dwell_score = min(1.0, dwell_ms / max(1.0, self.config.ground_dwell_time_ms_threshold))

        signals.append(
            DetectionSignal(
                name="prolonged_ground_dwell",
                value=dwell_ms,
                threshold=self.config.ground_dwell_time_ms_threshold,
                triggered=dwell_triggered,
                description=f"Prolonged recumbent position duration: {dwell_ms:.0f}ms without recovery",
            )
        )

        # Multi-signal Weighted Fusion
        overall_confidence = (
            (posture_score * self.config.weight_posture) +
            (velocity_score * self.config.weight_velocity) +
            (dwell_score * self.config.weight_ground_dwell)
        )
        overall_confidence = round(float(np.clip(overall_confidence, 0.0, 0.99)), 3)

        # Decision Logic
        if overall_confidence >= self.config.fall_confidence_threshold and is_horizontal and velocity_triggered:
            detection_type = DetectionType.POSSIBLE_FALL
            triggered_names = [s.name for s in signals if s.triggered]
            explanation = (
                f"Movement and posture dynamics are consistent with a POSSIBLE_FALL "
                f"(confidence: {overall_confidence:.2f}). Triggered signals: {', '.join(triggered_names)}."
            )
        elif is_horizontal and not velocity_triggered:
            detection_type = DetectionType.LYING_DOWN
            explanation = (
                f"Subject observed lying down or resting horizontally without preceding sudden downward impact "
                f"(confidence: {overall_confidence:.2f})."
            )
        elif velocity_triggered and not is_horizontal:
            detection_type = DetectionType.RAPID_DESCENT
            explanation = (
                f"Rapid vertical motion detected but subject recovered or maintained vertical posture."
            )
        else:
            detection_type = DetectionType.NORMAL_POSTURE
            explanation = "Normal upright or stable movement patterns observed across observation window."

        return DetectionResult(
            detection_type=detection_type,
            confidence=overall_confidence,
            model_name=DEFAULT_MODEL_NAME,
            model_version=DEFAULT_MODEL_VERSION,
            pipeline_version=DEFAULT_PIPELINE_VERSION,
            signals=signals,
            explanation=explanation,
            observation_window_ms=window_duration,
            frame_count_analyzed=len(sorted_seq),
            metadata={
                "aspect_ratio": aspect_ratio,
                "torso_angle": torso_angle,
                "max_downward_velocity": max_downward_velocity,
                "dwell_ms": dwell_ms,
            }
        )

    def _analyze_static_posture(self, frame: PoseFrame, count: int) -> DetectionResult:
        aspect_ratio, torso_angle = self._calculate_posture_features(frame)
        is_horizontal = (aspect_ratio is not None and aspect_ratio > self.config.aspect_ratio_fall_threshold) or \
                         (torso_angle is not None and torso_angle < self.config.torso_angle_fall_threshold)

        if is_horizontal:
            conf = 0.60
            return DetectionResult(
                detection_type=DetectionType.LYING_DOWN,
                confidence=conf,
                signals=[
                    DetectionSignal(
                        name="horizontal_posture",
                        value=aspect_ratio or 1.0,
                        threshold=self.config.aspect_ratio_fall_threshold,
                        triggered=True,
                        description="Static frame demonstrates horizontal posture",
                    )
                ],
                explanation="Static frame demonstrates horizontal body posture without temporal kinematic verification.",
                frame_count_analyzed=count,
            )
        else:
            return DetectionResult(
                detection_type=DetectionType.NORMAL_POSTURE,
                confidence=0.10,
                explanation="Static posture indicates upright or seated subject.",
                frame_count_analyzed=count,
            )

    def _calculate_posture_features(self, frame: PoseFrame) -> Tuple[Optional[float], Optional[float]]:
        aspect_ratio: Optional[float] = None
        torso_angle: Optional[float] = None

        if frame.bounding_box and len(frame.bounding_box) == 4:
            x_min, y_min, x_max, y_max = frame.bounding_box
            width = max(0.001, x_max - x_min)
            height = max(0.001, y_max - y_min)
            aspect_ratio = width / height

        # Torso Angle from shoulder and hip keypoints
        kp = frame.keypoints
        left_shoulder = kp.get("left_shoulder")
        right_shoulder = kp.get("right_shoulder")
        left_hip = kp.get("left_hip")
        right_hip = kp.get("right_hip")

        if left_shoulder and right_shoulder and left_hip and right_hip:
            mid_shoulder_x = (left_shoulder.x + right_shoulder.x) / 2.0
            mid_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2.0
            mid_hip_x = (left_hip.x + right_hip.x) / 2.0
            mid_hip_y = (left_hip.y + right_hip.y) / 2.0

            dx = mid_shoulder_x - mid_hip_x
            dy = mid_shoulder_y - mid_hip_y
            # Angle relative to horizontal ground (0 deg = flat, 90 deg = vertical)
            angle_rad = math.atan2(abs(dy), abs(dx))
            torso_angle = math.degrees(angle_rad)

        return aspect_ratio, torso_angle

    def _calculate_max_downward_velocity(self, sequence: List[PoseFrame]) -> float:
        max_vel = 0.0
        for i in range(1, len(sequence)):
            prev = sequence[i - 1]
            curr = sequence[i]
            dt_sec = max(0.001, (curr.timestamp_offset_ms - prev.timestamp_offset_ms) / 1000.0)

            # Center vertical position (y coordinate increases downwards in image space)
            prev_y = self._get_center_y(prev)
            curr_y = self._get_center_y(curr)

            if prev_y is not None and curr_y is not None:
                dy = curr_y - prev_y  # positive dy = downward displacement
                if dy > 0:
                    vel = dy / dt_sec
                    if vel > max_vel:
                        max_vel = vel
        return float(max_vel)

    def _get_center_y(self, frame: PoseFrame) -> Optional[float]:
        if frame.bounding_box and len(frame.bounding_box) == 4:
            return (frame.bounding_box[1] + frame.bounding_box[3]) / 2.0
        left_hip = frame.keypoints.get("left_hip")
        right_hip = frame.keypoints.get("right_hip")
        if left_hip and right_hip:
            return (left_hip.y + right_hip.y) / 2.0
        return None

    def _calculate_ground_dwell_time(self, sequence: List[PoseFrame]) -> float:
        dwell_ms = 0.0
        for i in range(1, len(sequence)):
            frame = sequence[i]
            prev = sequence[i - 1]
            aspect_ratio, torso_angle = self._calculate_posture_features(frame)
            is_horizontal = (aspect_ratio is not None and aspect_ratio > self.config.aspect_ratio_fall_threshold) or \
                             (torso_angle is not None and torso_angle < self.config.torso_angle_fall_threshold)
            if is_horizontal:
                dt = frame.timestamp_offset_ms - prev.timestamp_offset_ms
                if dt > 0:
                    dwell_ms += dt
        return float(dwell_ms)
