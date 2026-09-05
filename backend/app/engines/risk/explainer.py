"""Risk Explainer and Natural Language Explanation Generator.

Transforms deterministic signal metrics into human-interpretable operational
summaries for tourism authorities and safety operators.
"""

from typing import List
from backend.app.domain.models.enums import RiskLevel, RiskSignalType
from backend.app.engines.risk.signals import SignalResult


class RiskExplainer:
    """Generates concise, plain-language explanations for human operators."""

    @staticmethod
    def generate_explanation(
        risk_level: RiskLevel,
        risk_score: float,
        signals: List[SignalResult],
    ) -> str:
        # Filter active signals with meaningful contributions
        active_signals = [s for s in signals if s.score > 0.05 and s.contribution > 0.01]

        if not active_signals:
            if risk_level in (RiskLevel.SAFE, RiskLevel.LOW):
                return "Tourist is proceeding normally on the planned itinerary with nominal telemetry."
            return f"Overall risk is {risk_level.value} with baseline operational metrics within normal parameters."

        # Extract specific signal components
        phrases = []
        has_high_risk = any(s.signal_type == RiskSignalType.HIGH_RISK_ZONE for s in active_signals)
        has_restricted = any(s.signal_type == RiskSignalType.RESTRICTED_ZONE for s in active_signals)
        has_deviation = any(s.signal_type == RiskSignalType.ROUTE_DEVIATION for s in active_signals)
        has_inactivity = any(s.signal_type == RiskSignalType.PROLONGED_INACTIVITY for s in active_signals)
        has_speed = any(s.signal_type == RiskSignalType.UNUSUAL_SPEED for s in active_signals)
        has_zone_event = any(s.signal_type == RiskSignalType.ZONE_EVENT for s in active_signals)

        # Route deviation details
        dev_sig = next((s for s in active_signals if s.signal_type == RiskSignalType.ROUTE_DEVIATION), None)
        if dev_sig:
            dist_m = int(dev_sig.raw_value) if isinstance(dev_sig.raw_value, (int, float)) else dev_sig.raw_value
            if dev_sig.score > 0.7:
                phrases.append(f"significant route deviation ({dist_m}m from planned itinerary path)")
            elif dev_sig.score > 0.3:
                phrases.append(f"moderate deviation from planned trail ({dist_m}m off path)")
            else:
                phrases.append(f"minor variance from route ({dist_m}m)")

        # Zone containment details
        if has_high_risk:
            phrases.append("active location inside a high-risk safety perimeter")
        if has_restricted:
            phrases.append("entry into a restricted regulatory zone")

        # Inactivity details
        inact_sig = next((s for s in active_signals if s.signal_type == RiskSignalType.PROLONGED_INACTIVITY), None)
        if inact_sig:
            mins = int(inact_sig.raw_value) if isinstance(inact_sig.raw_value, (int, float)) else inact_sig.raw_value
            if inact_sig.score > 0.7:
                phrases.append(f"severe prolonged immobility ({mins} minutes stationary)")
            else:
                phrases.append(f"extended stationary period ({mins} minutes without progress)")

        # Unusual speed
        speed_sig = next((s for s in active_signals if s.signal_type == RiskSignalType.UNUSUAL_SPEED), None)
        if speed_sig:
            speed_kmh = int(speed_sig.raw_value * 3.6) if isinstance(speed_sig.raw_value, (int, float)) else speed_sig.raw_value
            phrases.append(f"unusual transport velocity detected ({speed_kmh} km/h)")

        # Zone transition event
        if has_zone_event:
            phrases.append("recent boundary entry event logged")

        # Computer Vision fall signal
        fall_sig = next((s for s in active_signals if s.signal_type == RiskSignalType.POSSIBLE_FALL), None)
        if fall_sig:
            phrases.append(f"computer vision detected possible fall kinematics ({fall_sig.raw_value})")

        # Compound sentence construction
        if not phrases:
            body = "Detected operational telemetry variances"
        elif len(phrases) == 1:
            body = phrases[0].capitalize()
        elif len(phrases) == 2:
            body = f"{phrases[0].capitalize()} combined with {phrases[1]}"
        else:
            body = f"{phrases[0].capitalize()}, {', '.join(phrases[1:-1])}, and {phrases[-1]}"

        return f"Risk evaluated as {risk_level.value} ({risk_score:.2f}): {body}."
