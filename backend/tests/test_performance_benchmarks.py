from datetime import datetime, timezone
import time
import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.domain.models.enums import RiskLevel, RecommendedAction, LocationFreshness, AuditEventType, AuditOutcome
from backend.app.domain.models.audit_event import AuditEvent
from backend.app.engines.risk.evaluator import RiskEvaluator
from backend.app.engines.audit.hasher import AuditHasher, GENESIS_HASH
from backend.app.engines.audit.verifier import AuditChainVerifier
from ml.interfaces import PoseFrame, Keypoint, DetectionType
from ml.models.fall_detector import FallDetector, FallDetectorConfig


def test_benchmark_api_health_latency(client: TestClient):
    """
    Benchmark core API latency on /api/v1/health across 50 iterations.
    """
    latencies = []
    for _ in range(50):
        start = time.perf_counter()
        resp = client.get("/api/v1/health")
        duration_ms = (time.perf_counter() - start) * 1000
        assert resp.status_code == 200
        latencies.append(duration_ms)

    avg_latency = sum(latencies) / len(latencies)
    p95_latency = sorted(latencies)[int(0.95 * len(latencies))]
    print(f"\n[BENCHMARK API Health] Mean: {avg_latency:.3f}ms, P95: {p95_latency:.3f}ms")
    assert avg_latency < 25.0  # Must be fast sub-25ms response in test


def test_benchmark_risk_evaluation_latency():
    """
    Benchmark deterministic Risk Engine evaluation latency across 100 cycles.
    """
    waypoints = [(34.9858, 135.7588), (34.9949, 135.7850), (35.0037, 135.7772)]
    active_zones = [{"id": "zone-1", "name": "Danger Cliff Zone", "zone_type": "HIGH_RISK"}]
    now = datetime(2026, 9, 5, 12, 0, 0, tzinfo=timezone.utc)

    latencies = []
    for _ in range(100):
        start = time.perf_counter()
        result = RiskEvaluator.evaluate(
            latitude=34.9900,
            longitude=135.7700,
            accuracy=4.5,
            speed=2.0,
            recorded_at=now,
            freshness=LocationFreshness.LIVE,
            waypoints=waypoints,
            active_zones=active_zones,
            location_history=[],
        )
        duration_ms = (time.perf_counter() - start) * 1000
        assert result.risk_score > 0
        latencies.append(duration_ms)

    avg_latency = sum(latencies) / len(latencies)
    p95_latency = sorted(latencies)[int(0.95 * len(latencies))]
    print(f"\n[BENCHMARK Risk Engine] Mean: {avg_latency:.4f}ms, P95: {p95_latency:.4f}ms")
    assert avg_latency < 5.0  # Sub-5ms deterministic evaluation


def test_benchmark_audit_hasher_and_chain_verifier():
    """
    Benchmark SHA-256 audit hash generation and 100-event chain verification.
    """
    # 1. Hashing benchmark
    hash_latencies = []
    prev = GENESIS_HASH
    events = []
    now = datetime(2026, 9, 5, 12, 0, 0, tzinfo=timezone.utc)
    for i in range(1, 101):
        details = {"action": f"benchmark_step_{i}", "val": i * 10}
        start = time.perf_counter()
        h = AuditHasher.calculate_event_hash(
            sequence_number=i,
            event_type="AUTH_LOGIN_SUCCESS",
            actor_id=None,
            actor_role="TOURIST",
            resource_type="USER",
            resource_id="user-bench-1",
            action="LOGIN",
            outcome="SUCCESS",
            details=details,
            previous_hash=prev,
            created_at=now,
        )
        duration_ms = (time.perf_counter() - start) * 1000
        hash_latencies.append(duration_ms)

        e = AuditEvent(
            sequence_number=i,
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            actor_id=None,
            actor_email="tourist@test.com",
            actor_role="TOURIST",
            resource_type="USER",
            resource_id="user-bench-1",
            action="LOGIN",
            outcome=AuditOutcome.SUCCESS,
            details=details,
            previous_hash=prev,
            event_hash=h,
        )
        e.created_at = now
        events.append(e)
        prev = h

    avg_hash = sum(hash_latencies) / len(hash_latencies)
    print(f"\n[BENCHMARK Audit Hasher] Mean: {avg_hash:.4f}ms")
    assert avg_hash < 2.0

    # 2. Chain verification benchmark across 100 events
    start_v = time.perf_counter()
    v_res = AuditChainVerifier.verify_chain(events)
    v_duration_ms = (time.perf_counter() - start_v) * 1000
    assert v_res.is_valid is True
    assert v_res.total_events_verified == 100
    print(f"[BENCHMARK Audit Verification (100 events)] Duration: {v_duration_ms:.3f}ms")
    assert v_duration_ms < 50.0


def test_benchmark_fall_detection_inference():
    """
    Benchmark kinematic fall detection inference latency across 100 iterations.
    """
    detector = FallDetector(FallDetectorConfig())
    # Create sample synthetic sequence
    seq = [
        PoseFrame(
            frame_index=0,
            timestamp_offset_ms=0.0,
            bounding_box=[0.4, 0.1, 0.6, 0.8],
            keypoints={
                "left_shoulder": Keypoint(x=0.45, y=0.25),
                "right_shoulder": Keypoint(x=0.55, y=0.25),
                "left_hip": Keypoint(x=0.45, y=0.55),
                "right_hip": Keypoint(x=0.55, y=0.55),
            },
        ),
        PoseFrame(
            frame_index=1,
            timestamp_offset_ms=400.0,
            bounding_box=[0.3, 0.3, 0.7, 0.9],
            keypoints={
                "left_shoulder": Keypoint(x=0.40, y=0.45),
                "right_shoulder": Keypoint(x=0.60, y=0.45),
                "left_hip": Keypoint(x=0.35, y=0.65),
                "right_hip": Keypoint(x=0.65, y=0.65),
            },
        ),
        PoseFrame(
            frame_index=2,
            timestamp_offset_ms=1000.0,
            bounding_box=[0.1, 0.6, 0.9, 0.95],
            keypoints={
                "left_shoulder": Keypoint(x=0.20, y=0.75),
                "right_shoulder": Keypoint(x=0.80, y=0.75),
                "left_hip": Keypoint(x=0.25, y=0.85),
                "right_hip": Keypoint(x=0.75, y=0.85),
            },
        ),
    ]

    latencies = []
    for _ in range(100):
        start = time.perf_counter()
        res = detector.analyze_pose_sequence(seq)
        duration_ms = (time.perf_counter() - start) * 1000
        assert res.detection_type is not None
        latencies.append(duration_ms)

    avg_latency = sum(latencies) / len(latencies)
    p95_latency = sorted(latencies)[int(0.95 * len(latencies))]
    print(f"\n[BENCHMARK Fall Detector Inference] Mean: {avg_latency:.4f}ms, P95: {p95_latency:.4f}ms")
    assert avg_latency < 2.0
