"""Risk Signal Extractors.

Modular, deterministic signal evaluation components that extract risk
features from real-time GPS telemetry, itinerary waypoints, and geozones.
"""

import math
from datetime import datetime, timezone
from typing import List, Tuple, Optional, Dict, Any

from backend.app.domain.models.enums import RiskSignalType, GeoZoneType, ZoneEventType
from backend.app.engines.risk.config import RiskConfig


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates geodesic distance between two points in meters using the Haversine formula."""
    r = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def point_to_segment_distance(
    p_lat: float, p_lon: float,
    a_lat: float, a_lon: float,
    b_lat: float, b_lon: float,
) -> float:
    """Calculates minimum distance from point P to line segment AB in meters."""
    # If A and B are effectively the same point
    ab_dist = haversine_distance(a_lat, a_lon, b_lat, b_lon)
    if ab_dist < 1.0:
        return haversine_distance(p_lat, p_lon, a_lat, a_lon)

    # Local equirectangular projection centered on segment
    mid_lat = math.radians((a_lat + b_lat) / 2.0)
    cos_mid = math.cos(mid_lat)

    # Segment vector (dx, dy) in projected meters
    seg_dx = math.radians(b_lon - a_lon) * 6371000.0 * cos_mid
    seg_dy = math.radians(b_lat - a_lat) * 6371000.0

    # Vector AP
    p_dx = math.radians(p_lon - a_lon) * 6371000.0 * cos_mid
    p_dy = math.radians(p_lat - a_lat) * 6371000.0

    # Projection scalar t = (AP . AB) / |AB|^2
    seg_len_sq = seg_dx * seg_dx + seg_dy * seg_dy
    if seg_len_sq == 0:
        return haversine_distance(p_lat, p_lon, a_lat, a_lon)

    t = (p_dx * seg_dx + p_dy * seg_dy) / seg_len_sq
    t = max(0.0, min(1.0, t))

    # Closest point C on segment AB
    c_lat = a_lat + t * (b_lat - a_lat)
    c_lon = a_lon + t * (b_lon - a_lon)

    return haversine_distance(p_lat, p_lon, c_lat, c_lon)


class SignalResult:
    def __init__(
        self,
        signal_type: RiskSignalType,
        score: float,
        weight: float,
        raw_value: Any,
        unit: str,
        description: str,
    ):
        self.signal_type = signal_type
        self.score = max(0.0, min(1.0, score))  # normalized [0, 1]
        self.weight = weight
        self.contribution = self.score * self.weight
        self.raw_value = raw_value
        self.unit = unit
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_type": self.signal_type.value,
            "score": round(self.score, 4),
            "weight": round(self.weight, 4),
            "contribution": round(self.contribution, 4),
            "raw_value": self.raw_value,
            "unit": self.unit,
            "description": self.description,
        }


class RouteDeviationEvaluator:
    """Evaluates cross-track distance between current position and planned route segments."""

    @staticmethod
    def evaluate(
        lat: float,
        lon: float,
        waypoints: List[Tuple[float, float]],
    ) -> Optional[SignalResult]:
        if not waypoints:
            # No planned itinerary route available
            return None

        min_dist = float("inf")

        if len(waypoints) == 1:
            min_dist = haversine_distance(lat, lon, waypoints[0][0], waypoints[0][1])
        else:
            for i in range(len(waypoints) - 1):
                a_lat, a_lon = waypoints[i]
                b_lat, b_lon = waypoints[i + 1]
                dist = point_to_segment_distance(lat, lon, a_lat, a_lon, b_lat, b_lon)
                if dist < min_dist:
                    min_dist = dist

        # Map distance to score using configured thresholds
        tol = RiskConfig.ROUTE_TOLERANCE_METERS
        mod = RiskConfig.ROUTE_MODERATE_METERS
        sev = RiskConfig.ROUTE_SEVERE_METERS

        if min_dist <= tol:
            score = 0.0
            desc = f"On planned route ({int(min_dist)}m from trail)"
        elif min_dist <= mod:
            # Linear scaling [100m, 300m] -> [0.0, 0.4]
            score = 0.4 * ((min_dist - tol) / (mod - tol))
            desc = f"Minor route deviation ({int(min_dist)}m from trail)"
        elif min_dist <= sev:
            # Linear scaling [300m, 800m] -> [0.4, 0.85]
            score = 0.4 + 0.45 * ((min_dist - mod) / (sev - mod))
            desc = f"Moderate route deviation ({int(min_dist)}m from planned path)"
        else:
            # Severe deviation > 800m
            excess = min(min_dist - sev, 2000.0)
            score = min(1.0, 0.85 + 0.15 * (excess / 2000.0))
            desc = f"Severe route deviation ({int(min_dist)}m from planned route)"

        return SignalResult(
            signal_type=RiskSignalType.ROUTE_DEVIATION,
            score=score,
            weight=RiskConfig.WEIGHT_ROUTE_DEVIATION,
            raw_value=round(min_dist, 1),
            unit="meters",
            description=desc,
        )


class ZoneRiskEvaluator:
    """Evaluates risk contributions from active geozone containment."""

    @staticmethod
    def evaluate(active_zones: List[Dict[str, Any]]) -> List[SignalResult]:
        results = []
        high_risk_zones = [z for z in active_zones if z.get("zone_type") == GeoZoneType.HIGH_RISK.value]
        restricted_zones = [z for z in active_zones if z.get("zone_type") == GeoZoneType.RESTRICTED.value]

        if high_risk_zones:
            zone_names = ", ".join(z.get("name", "Unknown") for z in high_risk_zones)
            results.append(
                SignalResult(
                    signal_type=RiskSignalType.HIGH_RISK_ZONE,
                    score=1.0,
                    weight=RiskConfig.WEIGHT_HIGH_RISK_ZONE,
                    raw_value=len(high_risk_zones),
                    unit="zones",
                    description=f"Located inside high-risk safety perimeter: {zone_names}",
                )
            )

        if restricted_zones:
            zone_names = ", ".join(z.get("name", "Unknown") for z in restricted_zones)
            results.append(
                SignalResult(
                    signal_type=RiskSignalType.RESTRICTED_ZONE,
                    score=1.0,
                    weight=RiskConfig.WEIGHT_RESTRICTED_ZONE,
                    raw_value=len(restricted_zones),
                    unit="zones",
                    description=f"Located inside restricted regulatory zone: {zone_names}",
                )
            )

        return results


class InactivityEvaluator:
    """Evaluates prolonged immobility or stopped state during an active journey."""

    @staticmethod
    def evaluate(
        current_lat: float,
        current_lon: float,
        current_time: datetime,
        location_history: List[Any],
    ) -> Optional[SignalResult]:
        if not location_history or len(location_history) < 2:
            return None

        def extract_point_info(item: Any):
            if isinstance(item, dict):
                lat = float(item.get("latitude", 0.0))
                lon = float(item.get("longitude", 0.0))
                t_val = item.get("recorded_at")
                if isinstance(t_val, str):
                    t = datetime.fromisoformat(t_val.replace("Z", "+00:00"))
                elif isinstance(t_val, datetime):
                    t = t_val
                else:
                    t = datetime.min.replace(tzinfo=timezone.utc)
            else:
                lat = float(getattr(item, "latitude", 0.0))
                lon = float(getattr(item, "longitude", 0.0))
                t = getattr(item, "recorded_at", datetime.min.replace(tzinfo=timezone.utc))
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            return lat, lon, t

        # Sort historical points descending by recorded_at
        parsed_history = [extract_point_info(pt) for pt in location_history]
        sorted_history = sorted(parsed_history, key=lambda x: x[2], reverse=True)

        stationary_since = current_time if current_time.tzinfo is not None else current_time.replace(tzinfo=timezone.utc)
        radius_threshold = RiskConfig.INACTIVITY_RADIUS_METERS

        for pt_lat, pt_lon, pt_time in sorted_history:
            dist = haversine_distance(current_lat, current_lon, pt_lat, pt_lon)
            if dist <= radius_threshold:
                stationary_since = pt_time
            else:
                # User was outside the radius before this point
                break

        curr_time = current_time if current_time.tzinfo is not None else current_time.replace(tzinfo=timezone.utc)
        stationary_minutes = max(0.0, (curr_time - stationary_since).total_seconds() / 60.0)

        th_min = RiskConfig.INACTIVITY_MINUTES_THRESHOLD  # 30 min
        th_sev = RiskConfig.INACTIVITY_MINUTES_SEVERE     # 60 min

        if stationary_minutes < 15.0:
            score = 0.0
            desc = f"Normal movement (stationary for {int(stationary_minutes)}m)"
        elif stationary_minutes <= th_min:
            score = 0.3 * ((stationary_minutes - 15.0) / (th_min - 15.0))
            desc = f"Extended rest stop ({int(stationary_minutes)} minutes stationary)"
        elif stationary_minutes <= th_sev:
            score = 0.3 + 0.5 * ((stationary_minutes - th_min) / (th_sev - th_min))
            desc = f"Prolonged inactivity ({int(stationary_minutes)} minutes stationary)"
        else:
            excess = min(stationary_minutes - th_sev, 120.0)
            score = min(1.0, 0.8 + 0.2 * (excess / 120.0))
            desc = f"Severe prolonged immobility ({int(stationary_minutes)} minutes stationary)"

        return SignalResult(
            signal_type=RiskSignalType.PROLONGED_INACTIVITY,
            score=score,
            weight=RiskConfig.WEIGHT_PROLONGED_INACTIVITY,
            raw_value=round(stationary_minutes, 1),
            unit="minutes",
            description=desc,
        )


class MovementSpeedEvaluator:
    """Evaluates anomalous speeds that deviate from expected journey mobility modes."""

    @staticmethod
    def evaluate(speed_mps: Optional[float]) -> Optional[SignalResult]:
        if speed_mps is None or speed_mps < 0.0:
            return None

        # Speed in m/s
        speed_kmh = speed_mps * 3.6

        if speed_mps > RiskConfig.VEHICLE_EXCESSIVE_SPEED_MPS:
            # > 137 km/h
            score = 0.9
            desc = f"Excessive vehicular speed ({int(speed_kmh)} km/h)"
        elif speed_mps > 25.0:
            # 90 km/h - 137 km/h
            score = 0.4
            desc = f"High speed transport detected ({int(speed_kmh)} km/h)"
        else:
            score = 0.0
            desc = f"Normal travel speed ({round(speed_kmh, 1)} km/h)"

        return SignalResult(
            signal_type=RiskSignalType.UNUSUAL_SPEED,
            score=score,
            weight=RiskConfig.WEIGHT_UNUSUAL_SPEED,
            raw_value=round(speed_mps, 2),
            unit="m/s",
            description=desc,
        )


class ZoneEventSignalEvaluator:
    """Evaluates recent boundary edge crossings into hazardous or restricted areas."""

    @staticmethod
    def evaluate(recent_events: List[Dict[str, Any]]) -> Optional[SignalResult]:
        if not recent_events:
            return None

        # Look for recent ENTER events into HIGH_RISK or RESTRICTED
        has_high_risk_enter = any(
            e.get("event_type") == ZoneEventType.ENTER.value and
            e.get("zone_type") == GeoZoneType.HIGH_RISK.value
            for e in recent_events
        )
        has_restricted_enter = any(
            e.get("event_type") == ZoneEventType.ENTER.value and
            e.get("zone_type") == GeoZoneType.RESTRICTED.value
            for e in recent_events
        )

        if has_high_risk_enter:
            return SignalResult(
                signal_type=RiskSignalType.ZONE_EVENT,
                score=1.0,
                weight=RiskConfig.WEIGHT_ZONE_EVENT,
                raw_value="ENTER_HIGH_RISK",
                unit="event",
                description="Recent boundary crossing into high-risk safety perimeter",
            )
        elif has_restricted_enter:
            return SignalResult(
                signal_type=RiskSignalType.ZONE_EVENT,
                score=0.7,
                weight=RiskConfig.WEIGHT_ZONE_EVENT,
                raw_value="ENTER_RESTRICTED",
                unit="event",
                description="Recent boundary crossing into restricted area",
            )

        return None


class FallDetectionSignalEvaluator:
    """Evaluates optional Computer Vision fall signals (e.g. POSSIBLE_FALL detection)."""

    @staticmethod
    def evaluate(cv_detection: Optional[Dict[str, Any]]) -> Optional[SignalResult]:
        if not cv_detection:
            return None

        detection_type = cv_detection.get("detection_type")
        confidence = float(cv_detection.get("confidence", 0.0))

        if detection_type == "POSSIBLE_FALL" and confidence >= 0.65:
            return SignalResult(
                signal_type=RiskSignalType.POSSIBLE_FALL,
                score=round(confidence, 2),
                weight=0.25,
                raw_value=f"POSSIBLE_FALL ({confidence:.2f})",
                unit="confidence",
                description=f"Computer Vision detected kinematics consistent with a possible fall (confidence: {confidence:.2f}).",
            )
        return None
