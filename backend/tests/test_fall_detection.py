import pytest
from ml.interfaces import PoseFrame, Keypoint, DetectionType
from ml.models.fall_detector import FallDetector, FallDetectorConfig


def test_fall_detection_on_upright_sequence():
    detector = FallDetector(FallDetectorConfig())
    seq = [
        PoseFrame(
            frame_index=i,
            timestamp_offset_ms=i * 500.0,
            bounding_box=[0.4, 0.1, 0.6, 0.8],  # Upright: width 0.2, height 0.7 -> aspect ~0.28
            keypoints={
                "left_shoulder": Keypoint(x=0.45, y=0.25),
                "right_shoulder": Keypoint(x=0.55, y=0.25),
                "left_hip": Keypoint(x=0.45, y=0.55),
                "right_hip": Keypoint(x=0.55, y=0.55),
            }
        )
        for i in range(4)
    ]
    result = detector.analyze_pose_sequence(seq)
    assert result.detection_type == DetectionType.NORMAL_POSTURE
    assert result.confidence < 0.50
    assert result.model_name == "kiroshi-fall-detector"
    assert result.model_version == "0.6.0"
    assert "NORMAL_POSTURE" in result.detection_type.value


def test_fall_detection_on_fall_sequence():
    detector = FallDetector(FallDetectorConfig(fall_confidence_threshold=0.65))
    seq = [
        # Frame 0: Standing upright
        PoseFrame(
            frame_index=0,
            timestamp_offset_ms=0.0,
            bounding_box=[0.4, 0.1, 0.6, 0.8],
            keypoints={
                "left_shoulder": Keypoint(x=0.45, y=0.25),
                "right_shoulder": Keypoint(x=0.55, y=0.25),
                "left_hip": Keypoint(x=0.45, y=0.55),
                "right_hip": Keypoint(x=0.55, y=0.55),
            }
        ),
        # Frame 1: Mid-fall rapid downward motion
        PoseFrame(
            frame_index=1,
            timestamp_offset_ms=300.0,
            bounding_box=[0.35, 0.45, 0.65, 0.85],
            keypoints={
                "left_shoulder": Keypoint(x=0.40, y=0.50),
                "right_shoulder": Keypoint(x=0.50, y=0.50),
                "left_hip": Keypoint(x=0.45, y=0.75),
                "right_hip": Keypoint(x=0.55, y=0.75),
            }
        ),
        # Frame 2: Ground impact (horizontal posture)
        PoseFrame(
            frame_index=2,
            timestamp_offset_ms=750.0,
            bounding_box=[0.2, 0.7, 0.8, 0.95],  # width 0.6, height 0.25 -> aspect 2.4
            keypoints={
                "left_shoulder": Keypoint(x=0.25, y=0.80),
                "right_shoulder": Keypoint(x=0.35, y=0.80),
                "left_hip": Keypoint(x=0.65, y=0.82),
                "right_hip": Keypoint(x=0.75, y=0.82),
            }
        ),
        # Frame 3: Ground dwell without recovery
        PoseFrame(
            frame_index=3,
            timestamp_offset_ms=2100.0,
            bounding_box=[0.2, 0.7, 0.8, 0.95],
            keypoints={
                "left_shoulder": Keypoint(x=0.25, y=0.80),
                "right_shoulder": Keypoint(x=0.35, y=0.80),
                "left_hip": Keypoint(x=0.65, y=0.82),
                "right_hip": Keypoint(x=0.75, y=0.82),
            }
        )
    ]
    result = detector.analyze_pose_sequence(seq)
    assert result.detection_type == DetectionType.POSSIBLE_FALL
    assert result.confidence >= 0.65
    assert len(result.signals) >= 3
    assert any(s.name == "horizontal_posture" and s.triggered for s in result.signals)
    assert any(s.name == "rapid_vertical_descent" and s.triggered for s in result.signals)
    assert any(s.name == "prolonged_ground_dwell" and s.triggered for s in result.signals)
    assert "POSSIBLE_FALL" in result.explanation


def test_fall_detection_on_empty_and_corrupted_inputs():
    detector = FallDetector()
    empty_res = detector.analyze_pose_sequence([])
    assert empty_res.detection_type == DetectionType.UNKNOWN
    assert empty_res.confidence == 0.0

    single_frame_res = detector.analyze_pose_sequence([
        PoseFrame(frame_index=0, timestamp_offset_ms=0.0, bounding_box=[0.4, 0.1, 0.6, 0.8])
    ])
    assert single_frame_res.detection_type == DetectionType.NORMAL_POSTURE
