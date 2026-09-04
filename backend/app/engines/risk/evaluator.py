"""Transparent Deterministic Risk Evaluation Engine.

Orchestrates signal extraction, weighted normalization, confidence scoring,
risk level classification, explainability, and recommended actions.
"""

from datetime import datetime, timezone
from typing import List, Tuple, Optional, Dict, Any

from backend.app.domain.models.enums import RiskLevel, RecommendedAction, LocationFreshness
from backend.app.engines.risk.config import RiskConfig
from backend.app.engines.risk.signals import (
    SignalResult,
    RouteDeviationEvaluator,
    ZoneRiskEvaluator,
    InactivityEvaluator,
    MovementSpeedEvaluator,
    ZoneEventSignalEvaluator,
)
from backend.app.engines.risk.explainer import RiskExplainer


class RiskEvaluationOutput:
    def __init__(
        self,
        risk_score: float,
        risk_level: RiskLevel,
        confidence: float,
        contributing_signals: List[Dict[str, Any]],
        explanation: str,
        recommended_action: RecommendedAction,
        model_version: str,
    ):
        self.risk_score = round(risk_score, 4)
        self.risk_level = risk_level
        self.confidence = round(confidence, 4)
        self.contributing_signals = contributing_signals
        self.explanation = explanation
        self.recommended_action = recommended_action
        self.model_version = model_version

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "confidence": self.confidence,
            "contributing_signals": self.contributing_signals,
            "explanation": self.explanation,
            "recommended_action": self.recommended_action.value,
            "model_version": self.model_version,
        }


class RiskEvaluator:
    """Deterministic, explainable safety risk evaluation engine."""

    @staticmethod
    def calculate_confidence(
        freshness: LocationFreshness,
        accuracy_meters: float,
        history_count: int,
        has_route_waypoints: bool,
    ) -> float:
        """Calculates confidence reflecting sensor data quality and context completeness."""
        # 1. Freshness Factor (30% weight)
        if freshness == LocationFreshness.LIVE:
            f_score = 1.0
        elif freshness == LocationFreshness.RECENT:
            f_score = 0.75
        elif freshness == LocationFreshness.STALE:
            f_score = 0.40
        else:
            f_score = 0.10

        # 2. Accuracy Factor (30% weight)
        if accuracy_meters <= 10.0:
            a_score = 1.0
        elif accuracy_meters <= 30.0:
            a_score = 0.85
        elif accuracy_meters <= 100.0:
            a_score = 0.60
        else:
            a_score = 0.30

        # 3. History Depth Factor (20% weight)
        if history_count >= 5:
            h_score = 1.0
        elif history_count >= 2:
            h_score = 0.70
        else:
            h_score = 0.40

        # 4. Route Waypoint Availability (20% weight)
        r_score = 1.0 if has_route_waypoints else 0.50

        confidence = 0.30 * f_score + 0.30 * a_score + 0.20 * h_score + 0.20 * r_score
        return max(0.10, min(1.0, confidence))

    @classmethod
    def evaluate(
        cls,
        latitude: float,
        longitude: float,
        accuracy: float,
        speed: Optional[float],
        recorded_at: datetime,
        freshness: LocationFreshness,
        waypoints: List[Tuple[float, float]],
        active_zones: List[Dict[str, Any]],
        location_history: List[Any],
        recent_zone_events: Optional[List[Dict[str, Any]]] = None,
    ) -> RiskEvaluationOutput:
        """Executes transparent deterministic evaluation across extracted signals."""
        extracted_signals: List[SignalResult] = []

        # 1. Route Deviation Signal
        route_sig = RouteDeviationEvaluator.evaluate(latitude, longitude, waypoints)
        if route_sig:
            extracted_signals.append(route_sig)

        # 2. Zone Containment Signals (HIGH_RISK, RESTRICTED)
        zone_sigs = ZoneRiskEvaluator.evaluate(active_zones)
        extracted_signals.extend(zone_sigs)

        # 3. Prolonged Inactivity Signal
        inact_sig = InactivityEvaluator.evaluate(latitude, longitude, recorded_at, location_history)
        if inact_sig:
            extracted_signals.append(inact_sig)

        # 4. Movement Speed Signal
        speed_sig = MovementSpeedEvaluator.evaluate(speed)
        if speed_sig:
            extracted_signals.append(speed_sig)

        # 5. Zone Event Signal
        if recent_zone_events:
            ze_sig = ZoneEventSignalEvaluator.evaluate(recent_zone_events)
            if ze_sig:
                extracted_signals.append(ze_sig)

        # Compute Raw Weighted Score
        raw_score = sum(sig.contribution for sig in extracted_signals)

        # Normalize score strictly between [0.0, 1.0]
        risk_score = max(0.0, min(1.0, raw_score))

        # Determine Categorical Level & Action Recommendation
        risk_level = RiskConfig.get_level_for_score(risk_score)
        recommended_action = RiskConfig.get_action_for_level(risk_level)

        # Calculate Meaningful Confidence
        history_count = len(location_history) if location_history else 0
        has_waypoints = len(waypoints) > 0
        confidence = cls.calculate_confidence(
            freshness=freshness,
            accuracy_meters=accuracy,
            history_count=history_count,
            has_route_waypoints=has_waypoints,
        )

        # Generate Human-Readable Explanation
        explanation = RiskExplainer.generate_explanation(
            risk_level=risk_level,
            risk_score=risk_score,
            signals=extracted_signals,
        )

        signal_dicts = [s.to_dict() for s in extracted_signals]

        return RiskEvaluationOutput(
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=confidence,
            contributing_signals=signal_dicts,
            explanation=explanation,
            recommended_action=recommended_action,
            model_version=RiskConfig.MODEL_VERSION,
        )
