"""Risk Engine Configuration and Policy Constants.

Defines model versioning, configurable risk thresholds, signal weights,
and physical tolerance thresholds. Centralized to prevent magic numbers.
"""

from typing import Dict
from backend.app.domain.models.enums import RiskLevel, RecommendedAction


class RiskConfig:
    # Model Identifier
    MODEL_VERSION: str = "v0.3-rule-engine"

    # Risk Level Thresholds (Normalized 0.0 to 1.0)
    # [0.00, 0.20) -> SAFE
    # [0.20, 0.40) -> LOW
    # [0.40, 0.65) -> MEDIUM
    # [0.65, 0.85) -> HIGH
    # [0.85, 1.00] -> CRITICAL
    THRESHOLD_SAFE_MAX: float = 0.20
    THRESHOLD_LOW_MAX: float = 0.40
    THRESHOLD_MEDIUM_MAX: float = 0.65
    THRESHOLD_HIGH_MAX: float = 0.85

    # Signal Weights (Base contributions before normalization)
    WEIGHT_ROUTE_DEVIATION: float = 0.35
    WEIGHT_HIGH_RISK_ZONE: float = 0.45
    WEIGHT_RESTRICTED_ZONE: float = 0.25
    WEIGHT_PROLONGED_INACTIVITY: float = 0.25
    WEIGHT_UNUSUAL_SPEED: float = 0.15
    WEIGHT_ZONE_EVENT: float = 0.15

    # Route Deviation Parameters (in meters)
    ROUTE_TOLERANCE_METERS: float = 100.0   # Normal GPS trail drift
    ROUTE_MODERATE_METERS: float = 300.0    # Noticeable off-trail movement
    ROUTE_SEVERE_METERS: float = 800.0      # Dangerous wilderness deviation

    # Inactivity Parameters
    INACTIVITY_RADIUS_METERS: float = 15.0  # Movement under 15m considered stationary
    INACTIVITY_MINUTES_THRESHOLD: float = 30.0  # 30 minutes stationary
    INACTIVITY_MINUTES_SEVERE: float = 60.0     # 60 minutes stationary

    # Movement Dynamics (Speed in m/s)
    WALKING_MAX_SPEED_MPS: float = 6.0      # ~21.6 km/h (running/sprinting max)
    VEHICLE_EXCESSIVE_SPEED_MPS: float = 38.0  # ~137 km/h (excessive speed in mountain terrain)

    # WebSocket Delta Broadcast Threshold
    # Broadcast if level changes OR score changes by >= 0.10
    RISK_DELTA_BROADCAST_THRESHOLD: float = 0.10

    @classmethod
    def get_level_for_score(cls, score: float) -> RiskLevel:
        """Determines the categorical risk level for a normalized score [0.0, 1.0]."""
        if score < cls.THRESHOLD_SAFE_MAX:
            return RiskLevel.SAFE
        elif score < cls.THRESHOLD_LOW_MAX:
            return RiskLevel.LOW
        elif score < cls.THRESHOLD_MEDIUM_MAX:
            return RiskLevel.MEDIUM
        elif score < cls.THRESHOLD_HIGH_MAX:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    # Class method alias for test naming compatibility
    score_to_level = get_level_for_score

    @classmethod
    def get_action_for_level(cls, level: RiskLevel) -> RecommendedAction:
        """Determines operator recommendation for a given risk level.
        Enforces human verification — NEVER automatically claims emergency.
        """
        if level == RiskLevel.SAFE:
            return RecommendedAction.MONITOR
        elif level == RiskLevel.LOW:
            return RecommendedAction.MONITOR
        elif level == RiskLevel.MEDIUM:
            return RecommendedAction.REVIEW
        elif level == RiskLevel.HIGH:
            return RecommendedAction.CONTACT_TOURIST
        else:
            return RecommendedAction.ESCALATE_FOR_HUMAN_REVIEW
