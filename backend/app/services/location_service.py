import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.domain.models.user import User
from backend.app.domain.models.trip import Trip
from backend.app.domain.models.location_event import LocationEvent
from backend.app.domain.models.enums import TripStatus, LocationFreshness, UserRole
from backend.app.schemas.location import LocationIngestRequest, LocationEventResponse, LiveTouristPosition
from backend.app.repositories.location_repository import LocationRepository
from backend.app.repositories.trip_repository import TripRepository
from backend.app.repositories.zone_repository import ZoneRepository
from backend.app.services.geospatial_service import GeospatialService
from backend.app.services.risk_service import RiskService
from backend.app.services.websocket_manager import ws_manager


class LocationService:
    def __init__(self, db: Session):
        self.db = db
        self.location_repo = LocationRepository(db)
        self.trip_repo = TripRepository(db)
        self.zone_repo = ZoneRepository(db)
        self.geo_service = GeospatialService(db)
        self.risk_service = RiskService(db)

    def calculate_freshness(self, recorded_at: datetime) -> LocationFreshness:
        now = datetime.now(timezone.utc)
        if recorded_at.tzinfo is None:
            recorded_at = recorded_at.replace(tzinfo=timezone.utc)
        
        diff = (now - recorded_at).total_seconds()
        if diff < 0:
            # Future timestamp within clock skew tolerance
            return LocationFreshness.LIVE
        elif diff <= settings.LOCATION_FRESHNESS_LIVE_SECONDS:
            return LocationFreshness.LIVE
        elif diff <= settings.LOCATION_FRESHNESS_RECENT_SECONDS:
            return LocationFreshness.RECENT
        else:
            return LocationFreshness.STALE

    async def ingest_location(
        self,
        current_user: User,
        payload: LocationIngestRequest,
    ) -> LocationEventResponse:
        # 1. Verify User Role
        if current_user.role != UserRole.TOURIST:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only registered tourists can submit real-time GPS locations.",
            )

        # 2. Validate Trip Existence and Ownership (Anti-IDOR)
        trip = self.trip_repo.get(payload.trip_id)
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trip with ID {payload.trip_id} not found.",
            )
        if trip.tourist_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot submit location data for another tourist's trip.",
            )

        # 3. Validate Trip Lifecycle State
        if trip.status != TripStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot record location for trip in '{trip.status.value}' status. Real-time tracking requires an ACTIVE trip.",
            )

        # 4. Validate Coordinates and Accuracy
        if not (-90.0 <= payload.latitude <= 90.0):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Latitude must be between -90.0 and 90.0 degrees.",
            )
        if not (-180.0 <= payload.longitude <= 180.0):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Longitude must be between -180.0 and 180.0 degrees.",
            )
        if payload.accuracy <= 0.0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Horizontal accuracy must be greater than zero.",
            )

        # 5. Validate Timestamp (Clock skew & historical limits)
        now_utc = datetime.now(timezone.utc)
        rec_at = payload.recorded_at
        if rec_at.tzinfo is None:
            rec_at = rec_at.replace(tzinfo=timezone.utc)

        # Check for future timestamp clock skew exceeding threshold
        if rec_at > now_utc + timedelta(seconds=settings.MAX_GPS_CLOCK_SKEW_SECONDS):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"GPS timestamp is too far in the future (exceeds {settings.MAX_GPS_CLOCK_SKEW_SECONDS}s clock skew tolerance).",
            )
        # Check for excessively stale GPS payload
        if rec_at < now_utc - timedelta(hours=settings.MAX_GPS_AGE_HOURS):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"GPS timestamp is older than the maximum allowable age ({settings.MAX_GPS_AGE_HOURS} hours).",
            )

        # 6. Build and Persist LocationEvent
        geom_wkt = self.geo_service.create_point_wkt(payload.longitude, payload.latitude)
        event = LocationEvent(
            tourist_id=current_user.id,
            trip_id=trip.id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            accuracy=payload.accuracy,
            altitude=payload.altitude,
            speed=payload.speed,
            heading=payload.heading,
            geom=geom_wkt,
            recorded_at=rec_at,
            received_at=now_utc,
        )
        saved_event = self.location_repo.create(event)

        # 7. Evaluate GeoZone transitions
        zone_events = self.geo_service.evaluate_zone_transitions(
            tourist_id=current_user.id,
            trip_id=trip.id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            recorded_at=rec_at,
            location_event_id=saved_event.id,
        )

        freshness = self.calculate_freshness(rec_at)

        # Retrieve currently occupied zones
        current_zone_states = self.zone_repo.get_tourist_current_zones(current_user.id)
        active_zone_names = [s.zone.name for s in current_zone_states if s.zone]
        active_zone_objects = [s.zone for s in current_zone_states if s.zone]

        # 8. Evaluate and Persist Explainable Risk Assessment (v0.3)
        risk_assessment = await self.risk_service.evaluate_and_persist(
            tourist_id=current_user.id,
            trip=trip,
            location_event=saved_event,
            active_zones=active_zone_objects,
            recent_zone_events=zone_events,
            freshness=freshness,
        )

        # 9. Broadcast to Authority WebSockets
        broadcast_payload = {
            "tourist_id": str(current_user.id),
            "tourist_name": current_user.full_name,
            "trip_id": str(trip.id),
            "trip_title": trip.title,
            "latitude": saved_event.latitude,
            "longitude": saved_event.longitude,
            "accuracy": saved_event.accuracy,
            "altitude": saved_event.altitude,
            "speed": saved_event.speed,
            "heading": saved_event.heading,
            "freshness": freshness.value,
            "risk_level": risk_assessment.risk_level.value,
            "risk_score": risk_assessment.risk_score,
            "active_zones": active_zone_names,
            "recorded_at": saved_event.recorded_at.isoformat(),
            "received_at": saved_event.received_at.isoformat(),
        }
        await ws_manager.broadcast_location_update(broadcast_payload)

        # Broadcast each zone event
        for ze in zone_events:
            zone_obj = self.zone_repo.get(ze.zone_id)
            await ws_manager.broadcast_zone_event(
                event_type=ze.event_type.value,
                payload={
                    "event_id": str(ze.id),
                    "tourist_id": str(current_user.id),
                    "tourist_name": current_user.full_name,
                    "trip_id": str(trip.id),
                    "zone_id": str(ze.zone_id),
                    "zone_name": zone_obj.name if zone_obj else "Unknown Zone",
                    "zone_type": zone_obj.zone_type.value if zone_obj else "SAFE",
                    "event_type": ze.event_type.value,
                    "occurred_at": ze.occurred_at.isoformat(),
                },
            )

        resp = LocationEventResponse.model_validate(saved_event)
        resp.freshness = freshness
        resp.risk_level = risk_assessment.risk_level.value
        resp.risk_score = risk_assessment.risk_score
        return resp

    def get_trip_history(
        self,
        current_user: User,
        trip_id: uuid.UUID,
        limit: int = 500,
    ) -> List[LocationEventResponse]:
        trip = self.trip_repo.get(trip_id)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found.")
        
        # Authorization: Authority, Admin, or owning Tourist
        if current_user.role not in [UserRole.AUTHORITY, UserRole.ADMIN] and trip.tourist_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized to view location history for this trip.")

        events = self.location_repo.get_history_for_trip(trip_id, limit=limit)
        results = []
        for e in events:
            r = LocationEventResponse.model_validate(e)
            r.freshness = self.calculate_freshness(e.recorded_at)
            results.append(r)
        return results

    def get_active_tourists_snapshot(self) -> List[LiveTouristPosition]:
        latest_events = self.location_repo.get_active_tourists_latest()
        snapshot = []
        for e in latest_events:
            tourist = e.tourist
            trip = e.trip
            if not tourist or not trip or trip.status != TripStatus.ACTIVE:
                continue

            current_zones = self.zone_repo.get_tourist_current_zones(tourist.id)
            active_zone_names = [s.zone.name for s in current_zones if s.zone]

            latest_risk = self.risk_service.risk_repo.get_latest_for_trip(trip.id)
            risk_level_val = latest_risk.risk_level.value if latest_risk else None
            risk_score_val = latest_risk.risk_score if latest_risk else None

            snapshot.append(
                LiveTouristPosition(
                    tourist_id=tourist.id,
                    tourist_name=tourist.full_name,
                    trip_id=trip.id,
                    trip_title=trip.title,
                    latitude=e.latitude,
                    longitude=e.longitude,
                    accuracy=e.accuracy,
                    altitude=e.altitude,
                    speed=e.speed,
                    heading=e.heading,
                    freshness=self.calculate_freshness(e.recorded_at),
                    risk_level=risk_level_val,
                    risk_score=risk_score_val,
                    recorded_at=e.recorded_at,
                    received_at=e.received_at,
                    active_zones=active_zone_names,
                )
            )
        return snapshot
