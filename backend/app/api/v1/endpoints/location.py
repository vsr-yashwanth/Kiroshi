import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.domain.models.user import User
from backend.app.domain.models.enums import UserRole
from backend.app.api.deps import get_current_user, require_role
from backend.app.schemas.location import (
    LocationIngestRequest,
    LocationEventResponse,
    LiveTouristPosition,
)
from backend.app.services.location_service import LocationService

router = APIRouter()


@router.post(
    "",
    response_model=LocationEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest real-time GPS location",
    description="Authenticates the tourist, validates coordinates and active trip state, persists the point, checks GeoZones, and broadcasts updates.",
)
async def ingest_location(
    payload: LocationIngestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = LocationService(db)
    return await service.ingest_location(current_user=current_user, payload=payload)


@router.get(
    "/history/{trip_id}",
    response_model=List[LocationEventResponse],
    summary="Get location trail history for a trip",
    description="Returns recorded GPS breadcrumbs for an active or completed trip. Accessible by owning tourist or authority.",
)
def get_trip_location_history(
    trip_id: uuid.UUID,
    limit: int = Query(default=500, ge=1, le=2000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = LocationService(db)
    return service.get_trip_history(current_user=current_user, trip_id=trip_id, limit=limit)


@router.get(
    "/active",
    response_model=List[LiveTouristPosition],
    summary="Get active tourists live positions",
    description="Returns the latest location, freshness status, and active zone occupancy for all tourists on active trips.",
)
def get_active_tourists_live(
    current_user: User = Depends(require_role(UserRole.AUTHORITY, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    service = LocationService(db)
    return service.get_active_tourists_snapshot()
