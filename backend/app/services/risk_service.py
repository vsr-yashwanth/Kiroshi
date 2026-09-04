import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.logging import logger
from backend.app.domain.models.enums import (
    LocationFreshness,
    RecommendedAction,
    RiskLevel,
    TripStatus,
    UserRole,
)
from backend.app.domain.models.geo_zone import GeoZone
from backend.app.domain.models.location_event import LocationEvent
from backend.app.domain.models.risk_assessment import RiskAssessment
from backend.app.domain.models.trip import Trip
from backend.app.domain.models.user import User
from backend.app.domain.models.zone_event import ZoneEvent
from backend.app.engines.risk.config import RiskConfig
from backend.app.engines.risk.evaluator import RiskEvaluator
from backend.app.repositories.location_repository import LocationRepository
from backend.app.repositories.risk_repository import RiskRepository
from backend.app.repositories.trip_repository import TripRepository
from backend.app.repositories.zone_repository import ZoneRepository
from backend.app.schemas.risk import LiveTouristRiskSnapshot
from backend.app.services.websocket_manager import ws_manager


class RiskService:
    def __init__(self, db: Session):
        self.db = db
        self.risk_repo = RiskRepository(db)
        self.location_repo = LocationRepository(db)
        self.trip_repo = TripRepository(db)
        self.zone_repo = ZoneRepository(db)

    async def evaluate_and_persist(
        self,
        tourist_id: uuid.UUID,
        trip: Trip,
        location_event: LocationEvent,
        active_zones: list[GeoZone],
        recent_zone_events: list[ZoneEvent] | None = None,
        freshness: LocationFreshness = LocationFreshness.LIVE,
    ) -> RiskAssessment:
        # 1. Gather itinerary waypoints (ordered by sequence_order)
        waypoints = []
        if trip.itineraries:
            sorted_itin = sorted(trip.itineraries, key=lambda x: x.sequence_order)
            waypoints = [(it.latitude, it.longitude) for it in sorted_itin]

        # 2. Gather recent trajectory history
        location_history = self.location_repo.get_history_for_trip(trip.id, limit=25)

        # 3. Format active zones
        active_zone_dicts = [
            {
                "id": str(z.id),
                "name": z.name,
                "zone_type": z.zone_type.value if hasattr(z.zone_type, "value") else str(z.zone_type),
            }
            for z in active_zones
        ]

        # 4. Format recent zone events
        recent_event_dicts = []
        if recent_zone_events:
            for ze in recent_zone_events:
                z_type = "SAFE"
                if ze.zone and hasattr(ze.zone, "zone_type"):
                    z_type = ze.zone.zone_type.value if hasattr(ze.zone.zone_type, "value") else str(ze.zone.zone_type)
                recent_event_dicts.append({
                    "event_type": ze.event_type.value if hasattr(ze.event_type, "value") else str(ze.event_type),
                    "zone_type": z_type,
                })

        # 5. Fetch previous risk assessment for delta comparison
        prev_assessment = self.risk_repo.get_latest_for_trip(trip.id)

        # 6. Evaluate deterministic risk
        output = RiskEvaluator.evaluate(
            latitude=location_event.latitude,
            longitude=location_event.longitude,
            accuracy=location_event.accuracy,
            speed=location_event.speed,
            recorded_at=location_event.recorded_at,
            freshness=freshness,
            waypoints=waypoints,
            active_zones=active_zone_dicts,
            location_history=location_history,
            recent_zone_events=recent_event_dicts,
        )

        # 7. Persist RiskAssessment
        assessment = RiskAssessment(
            tourist_id=tourist_id,
            trip_id=trip.id,
            location_event_id=location_event.id,
            risk_score=output.risk_score,
            risk_level=output.risk_level,
            confidence=output.confidence,
            contributing_signals=output.contributing_signals,
            explanation=output.explanation,
            recommended_action=output.recommended_action,
            model_version=output.model_version,
        )
        saved = self.risk_repo.create(assessment)

        # 8. Determine if real-time broadcast is warranted
        # Meaningful change: initial non-zero risk, level changed, score delta >= threshold, or signals changed
        is_meaningful = False
        if prev_assessment is None:
            if saved.risk_level != RiskLevel.SAFE or saved.risk_score > 0.0:
                is_meaningful = True
        elif (
            prev_assessment.risk_level != saved.risk_level
            or abs(saved.risk_score - prev_assessment.risk_score) >= RiskConfig.RISK_DELTA_BROADCAST_THRESHOLD
        ):
            is_meaningful = True
        else:
            curr_signal_types = {s.get("signal_type") for s in (saved.contributing_signals or []) if isinstance(s, dict)}
            prev_signal_types = {s.get("signal_type") for s in (prev_assessment.contributing_signals or []) if isinstance(s, dict)}
            if curr_signal_types != prev_signal_types:
                is_meaningful = True

        if is_meaningful:
            level_str = saved.risk_level.value if hasattr(saved.risk_level, "value") else str(saved.risk_level)
            action_str = (
                saved.recommended_action.value
                if hasattr(saved.recommended_action, "value")
                else str(saved.recommended_action)
            )
            assessed_time_str = (
                saved.created_at.isoformat()
                if saved.created_at
                else datetime.now(timezone.utc).isoformat()
            )
            broadcast_payload = {
                "assessment_id": str(saved.id),
                "tourist_id": str(tourist_id),
                "trip_id": str(trip.id),
                "trip_title": trip.title,
                "risk_score": saved.risk_score,
                "risk_level": level_str,
                "confidence": saved.confidence,
                "explanation": saved.explanation,
                "recommended_action": action_str,
                "contributing_signals": saved.contributing_signals,
                "model_version": saved.model_version,
                "assessed_at": assessed_time_str,
            }
            await ws_manager.broadcast_risk_update(broadcast_payload)
            logger.info(
                f"Risk update broadcast: tourist={tourist_id}, level={level_str}, score={saved.risk_score}"
            )

        # 9. Phase 15: Signal incident detection if critical risk threshold reached
        if (
            saved.risk_level == RiskLevel.CRITICAL
            or saved.recommended_action == RecommendedAction.ESCALATE_FOR_HUMAN_REVIEW
        ):
            try:
                from backend.app.services.incident_service import IncidentService
                incident_svc = IncidentService(self.db)
                await incident_svc.create_from_risk(saved)
            except Exception as e:
                logger.error(f"Error creating incident from risk evaluation: {e}")

        return saved

    def get_current_risk_for_tourist(
        self,
        current_user: User,
        tourist_id: uuid.UUID,
    ) -> RiskAssessment | None:
        # RBAC: Tourist can only query own risk
        if current_user.role == UserRole.TOURIST and current_user.id != tourist_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot view risk assessment for another tourist.",
            )
        return self.risk_repo.get_latest_for_tourist(tourist_id)

    def get_trip_risk_history(
        self,
        current_user: User,
        trip_id: uuid.UUID,
        limit: int = 100,
    ) -> list[RiskAssessment]:
        trip = self.trip_repo.get(trip_id)
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found.",
            )

        # RBAC: Tourist can only query own trip history
        if current_user.role == UserRole.TOURIST and trip.tourist_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot view risk history for another tourist's trip.",
            )

        return self.risk_repo.get_history_for_trip(trip_id, limit=limit)

    def get_active_tourists_risk_snapshot(
        self,
        current_user: User,
    ) -> list[LiveTouristRiskSnapshot]:
        # RBAC: Authority or Admin only
        if current_user.role not in [UserRole.AUTHORITY, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authority privileges required to view system-wide active risk snapshot.",
            )

        active_trips = self.trip_repo.get_all_trips(status=TripStatus.ACTIVE)
        snapshots = []
        for trip in active_trips:
            tourist = trip.tourist
            if not tourist:
                continue

            latest_risk = self.risk_repo.get_latest_for_trip(trip.id)
            if latest_risk:
                snapshots.append(
                    LiveTouristRiskSnapshot(
                        tourist_id=tourist.id,
                        tourist_name=tourist.full_name,
                        trip_id=trip.id,
                        trip_title=trip.title,
                        risk_score=latest_risk.risk_score,
                        risk_level=latest_risk.risk_level,
                        confidence=latest_risk.confidence,
                        explanation=latest_risk.explanation,
                        recommended_action=latest_risk.recommended_action,
                        model_version=latest_risk.model_version,
                        assessed_at=latest_risk.created_at,
                    )
                )
        return snapshots
