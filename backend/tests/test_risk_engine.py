import pytest
from datetime import datetime, timezone, timedelta
from backend.app.domain.models.enums import RiskLevel, RecommendedAction, RiskSignalType, LocationFreshness
from backend.app.engines.risk.config import RiskConfig
from backend.app.engines.risk.evaluator import RiskEvaluator
from backend.app.engines.risk.explainer import RiskExplainer
from backend.app.engines.risk.signals import (
    RouteDeviationEvaluator,
    ZoneRiskEvaluator,
    InactivityEvaluator,
    MovementSpeedEvaluator,
    ZoneEventSignalEvaluator,
)


class TestRiskEngineScenarios:
    """
    Deterministic unit tests for KIROSHI v0.3 Risk Engine.
    Covers Scenarios A through H as specified in AI_PROMPTS/03_V0.3_RISK_ENGINE.md.
    """

    @pytest.fixture
    def route_waypoints(self):
        # Linear route: Kyoto Station -> Kiyomizu-dera -> Yasaka Shrine
        return [
            (34.9858, 135.7588),
            (34.9949, 135.7850),
            (35.0037, 135.7772),
        ]

    def test_scenario_a_tourist_remains_on_route(self, route_waypoints):
        """
        SCENARIO A: Tourist remains directly on the planned itinerary route.
        Expected: SAFE (score < 0.20).
        """
        # Exact midpoint between waypoint 0 and 1
        lat = (34.9858 + 34.9949) / 2
        lng = (135.7588 + 135.7850) / 2

        output = RiskEvaluator.evaluate(
            latitude=lat,
            longitude=lng,
            accuracy=5.0,
            speed=1.4,
            recorded_at=datetime(2026, 9, 4, 12, 0, 0, tzinfo=timezone.utc),
            freshness=LocationFreshness.LIVE,
            waypoints=route_waypoints,
            active_zones=[],
            location_history=[],
        )

        assert output.risk_level in [RiskLevel.SAFE, RiskLevel.LOW]
        assert output.risk_score < 0.20
        assert output.recommended_action == RecommendedAction.MONITOR
        assert output.model_version == RiskConfig.MODEL_VERSION
        assert "nominal" in output.explanation.lower() or "normally" in output.explanation.lower()

    def test_scenario_b_tourist_enters_restricted_zone(self, route_waypoints):
        """
        SCENARIO B: Tourist enters a RESTRICTED zone.
        Expected: Risk increases with RESTRICTED_ZONE signal.
        """
        lat, lng = route_waypoints[0]
        active_zones = [
            {"id": "zone-1", "name": "Imperial Palace Closed Grounds", "zone_type": "RESTRICTED"}
        ]

        output = RiskEvaluator.evaluate(
            latitude=lat,
            longitude=lng,
            accuracy=5.0,
            speed=1.2,
            recorded_at=datetime(2026, 9, 4, 12, 0, 0, tzinfo=timezone.utc),
            freshness=LocationFreshness.LIVE,
            waypoints=route_waypoints,
            active_zones=active_zones,
            location_history=[],
        )

        assert output.risk_score >= 0.25
        assert output.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]
        signal_types = [s["signal_type"] for s in output.contributing_signals]
        assert RiskSignalType.RESTRICTED_ZONE.value in signal_types
        assert "restricted" in output.explanation.lower()

    def test_scenario_c_tourist_enters_high_risk_zone(self, route_waypoints):
        """
        SCENARIO C: Tourist enters a HIGH_RISK hazard zone.
        Expected: Risk increases substantially with HIGH_RISK_ZONE signal.
        """
        lat, lng = route_waypoints[0]
        active_zones = [
            {"id": "zone-hazard", "name": "Active Landslide Ridge", "zone_type": "HIGH_RISK"}
        ]

        output = RiskEvaluator.evaluate(
            latitude=lat,
            longitude=lng,
            accuracy=5.0,
            speed=1.0,
            recorded_at=datetime(2026, 9, 4, 12, 0, 0, tzinfo=timezone.utc),
            freshness=LocationFreshness.LIVE,
            waypoints=route_waypoints,
            active_zones=active_zones,
            location_history=[],
        )

        assert output.risk_score >= 0.40
        assert output.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]
        signal_types = [s["signal_type"] for s in output.contributing_signals]
        assert RiskSignalType.HIGH_RISK_ZONE.value in signal_types
        assert "high-risk" in output.explanation.lower() or "perimeter" in output.explanation.lower() or "hazard" in output.explanation.lower()

    def test_scenario_d_tourist_deviates_from_route(self, route_waypoints):
        """
        SCENARIO D: Tourist deviates significantly from the planned route.
        Expected: Route deviation contributes to risk score.
        """
        # Coordinate ~1.5 km away from Kyoto route
        off_route_lat = 34.9500
        off_route_lng = 135.7200

        output = RiskEvaluator.evaluate(
            latitude=off_route_lat,
            longitude=off_route_lng,
            accuracy=6.0,
            speed=1.5,
            recorded_at=datetime(2026, 9, 4, 12, 0, 0, tzinfo=timezone.utc),
            freshness=LocationFreshness.LIVE,
            waypoints=route_waypoints,
            active_zones=[],
            location_history=[],
        )

        assert output.risk_score > 0.15
        signal_types = [s["signal_type"] for s in output.contributing_signals]
        assert RiskSignalType.ROUTE_DEVIATION.value in signal_types
        assert "deviation" in output.explanation.lower()

    def test_scenario_e_tourist_deviates_and_remains_inactive(self, route_waypoints):
        """
        SCENARIO E: Tourist deviates and remains completely inactive (>30 mins).
        Expected: Combined route deviation + prolonged inactivity elevates risk to HIGH.
        """
        off_route_lat = 34.9300
        off_route_lng = 135.7000
        now = datetime(2026, 9, 4, 12, 45, 0, tzinfo=timezone.utc)

        # Generate 10 identical stationary history points over the last 40 minutes
        history = []
        for i in range(10):
            t = now - timedelta(minutes=40 - (i * 4))
            history.append({
                "latitude": off_route_lat,
                "longitude": off_route_lng,
                "speed": 0.0,
                "accuracy": 4.0,
                "recorded_at": t.isoformat(),
            })

        output = RiskEvaluator.evaluate(
            latitude=off_route_lat,
            longitude=off_route_lng,
            accuracy=4.0,
            speed=0.0,
            recorded_at=now,
            freshness=LocationFreshness.LIVE,
            waypoints=route_waypoints,
            active_zones=[],
            location_history=history,
        )

        signal_types = [s["signal_type"] for s in output.contributing_signals]
        assert RiskSignalType.ROUTE_DEVIATION.value in signal_types
        assert RiskSignalType.PROLONGED_INACTIVITY.value in signal_types
        assert output.risk_score >= 0.45
        assert output.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]
        assert output.recommended_action in [RecommendedAction.CONTACT_TOURIST, RecommendedAction.ESCALATE_FOR_HUMAN_REVIEW, RecommendedAction.REVIEW]

    def test_scenario_f_tourist_displays_unusual_speed(self, route_waypoints):
        """
        SCENARIO F: Tourist displays unusual speed (>35 m/s or 126 km/h).
        Expected: UNUSUAL_SPEED signal contributes to risk.
        """
        lat, lng = route_waypoints[0]

        output = RiskEvaluator.evaluate(
            latitude=lat,
            longitude=lng,
            accuracy=5.0,
            speed=42.0,  # ~151 km/h
            recorded_at=datetime(2026, 9, 4, 12, 0, 0, tzinfo=timezone.utc),
            freshness=LocationFreshness.LIVE,
            waypoints=route_waypoints,
            active_zones=[],
            location_history=[],
        )

        signal_types = [s["signal_type"] for s in output.contributing_signals]
        assert RiskSignalType.UNUSUAL_SPEED.value in signal_types
        assert "speed" in output.explanation.lower() or "velocity" in output.explanation.lower()

    def test_scenario_g_multiple_signals_simultaneous_critical(self, route_waypoints):
        """
        SCENARIO G: Simultaneous route deviation, restricted hazard zone entry, and inactivity.
        Expected: Combined score is deterministic, escalates to HIGH/CRITICAL, and produces clear explanation.
        """
        off_lat = 34.9300
        off_lng = 135.7000
        now = datetime(2026, 9, 4, 13, 0, 0, tzinfo=timezone.utc)

        history = [
            {
                "latitude": off_lat,
                "longitude": off_lng,
                "speed": 0.0,
                "accuracy": 3.0,
                "recorded_at": (now - timedelta(minutes=45)).isoformat(),
            },
            {
                "latitude": off_lat,
                "longitude": off_lng,
                "speed": 0.0,
                "accuracy": 3.0,
                "recorded_at": now.isoformat(),
            }
        ]
        active_zones = [
            {"id": "zone-hazard", "name": "Deep Forest Ravine", "zone_type": "HIGH_RISK"}
        ]

        output = RiskEvaluator.evaluate(
            latitude=off_lat,
            longitude=off_lng,
            accuracy=4.0,
            speed=0.0,
            recorded_at=now,
            freshness=LocationFreshness.LIVE,
            waypoints=route_waypoints,
            active_zones=active_zones,
            location_history=history,
        )

        assert output.risk_score >= 0.70
        assert output.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert output.recommended_action == RecommendedAction.ESCALATE_FOR_HUMAN_REVIEW
        assert len(output.contributing_signals) >= 3

    def test_scenario_h_stale_data_reduces_confidence(self, route_waypoints):
        """
        SCENARIO H: Stale telemetry with poor GPS accuracy and no route context.
        Expected: Confidence metric drops significantly.
        """
        output_live = RiskEvaluator.evaluate(
            latitude=35.0,
            longitude=135.0,
            accuracy=4.0,
            speed=1.0,
            recorded_at=datetime(2026, 9, 4, 12, 0, 0, tzinfo=timezone.utc),
            freshness=LocationFreshness.LIVE,
            waypoints=route_waypoints,
            active_zones=[],
            location_history=[{"latitude": 35.0, "longitude": 135.0, "recorded_at": "..."}],
        )

        output_stale = RiskEvaluator.evaluate(
            latitude=35.0,
            longitude=135.0,
            accuracy=120.0,  # Poor accuracy
            speed=1.0,
            recorded_at=datetime(2026, 9, 4, 10, 0, 0, tzinfo=timezone.utc),
            freshness=LocationFreshness.STALE,  # Stale data
            waypoints=[],  # No route context
            active_zones=[],
            location_history=[],  # No history
        )

        assert output_stale.confidence < output_live.confidence
        assert output_stale.confidence <= 0.45


class TestRiskThresholdBoundaries:
    """
    Boundary value testing for all configured risk thresholds:
    SAFE: [0.00, 0.20)
    LOW: [0.20, 0.40)
    MEDIUM: [0.40, 0.65)
    HIGH: [0.65, 0.85)
    CRITICAL: [0.85, 1.00]
    """

    @pytest.mark.parametrize(
        "score,expected_level",
        [
            (0.00, RiskLevel.SAFE),
            (0.10, RiskLevel.SAFE),
            (0.199, RiskLevel.SAFE),
            (0.20, RiskLevel.LOW),
            (0.25, RiskLevel.LOW),
            (0.399, RiskLevel.LOW),
            (0.40, RiskLevel.MEDIUM),
            (0.50, RiskLevel.MEDIUM),
            (0.649, RiskLevel.MEDIUM),
            (0.65, RiskLevel.HIGH),
            (0.75, RiskLevel.HIGH),
            (0.849, RiskLevel.HIGH),
            (0.85, RiskLevel.CRITICAL),
            (0.95, RiskLevel.CRITICAL),
            (1.00, RiskLevel.CRITICAL),
        ],
    )
    def test_threshold_classification(self, score, expected_level):
        assigned_level = RiskConfig.score_to_level(score)
        assert assigned_level == expected_level

    def test_score_normalization_bounds(self):
        """Scores must strictly clamp to [0.0, 1.0]."""
        assert RiskConfig.score_to_level(-0.5) == RiskLevel.SAFE
        assert RiskConfig.score_to_level(1.5) == RiskLevel.CRITICAL


class TestRiskEngineDeterminism:
    """
    Phase 17 — Determinism verification.
    Same inputs + same config + same model version MUST yield identical output across iterations.
    """

    def test_determinism_across_100_runs(self):
        waypoints = [(35.0, 135.0), (35.1, 135.1)]
        active_zones = [{"id": "z1", "name": "Restricted Sector", "zone_type": "RESTRICTED"}]
        history = [
            {
                "latitude": 35.05,
                "longitude": 135.05,
                "accuracy": 8.0,
                "speed": 0.0,
                "recorded_at": "2026-09-04T12:00:00Z",
            }
        ]

        baseline = RiskEvaluator.evaluate(
            latitude=35.08,
            longitude=135.08,
            accuracy=7.5,
            speed=0.0,
            recorded_at=datetime(2026, 9, 4, 12, 35, 0, tzinfo=timezone.utc),
            freshness=LocationFreshness.LIVE,
            waypoints=waypoints,
            active_zones=active_zones,
            location_history=history,
        )

        for _ in range(100):
            run = RiskEvaluator.evaluate(
                latitude=35.08,
                longitude=135.08,
                accuracy=7.5,
                speed=0.0,
                recorded_at=datetime(2026, 9, 4, 12, 35, 0, tzinfo=timezone.utc),
                freshness=LocationFreshness.LIVE,
                waypoints=waypoints,
                active_zones=active_zones,
                location_history=history,
            )

            assert run.risk_score == baseline.risk_score
            assert run.risk_level == baseline.risk_level
            assert run.confidence == baseline.confidence
            assert run.recommended_action == baseline.recommended_action
            assert run.explanation == baseline.explanation
            assert run.model_version == baseline.model_version
            assert len(run.contributing_signals) == len(baseline.contributing_signals)
