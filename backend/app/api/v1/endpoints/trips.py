from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_active_user
from backend.app.domain.models.user import User
from backend.app.domain.models.enums import TripStatus
from backend.app.services.trip_service import TripService
from backend.app.schemas.trip import TripCreate, TripUpdate, TripResponse

router = APIRouter()


@router.get("", response_model=List[TripResponse])
def list_trips(
    status: Optional[TripStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    trip_service = TripService(db)
    trips = trip_service.list_trips(
        user=current_user,
        status=status,
        skip=skip,
        limit=limit,
    )
    return [TripResponse.model_validate(t) for t in trips]


@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def create_trip(
    trip_in: TripCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    trip_service = TripService(db)
    trip = trip_service.create_trip(user=current_user, trip_in=trip_in)
    return TripResponse.model_validate(trip)


@router.get("/{id}", response_model=TripResponse)
def get_trip(
    id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    trip_service = TripService(db)
    trip = trip_service.get_trip(user=current_user, trip_id=id)
    return TripResponse.model_validate(trip)


@router.patch("/{id}", response_model=TripResponse)
def update_trip(
    id: UUID,
    trip_in: TripUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    trip_service = TripService(db)
    trip = trip_service.update_trip(user=current_user, trip_id=id, trip_in=trip_in)
    return TripResponse.model_validate(trip)


@router.post("/{id}/start", response_model=TripResponse)
def start_trip(
    id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    trip_service = TripService(db)
    trip = trip_service.start_trip(user=current_user, trip_id=id)
    return TripResponse.model_validate(trip)


@router.post("/{id}/stop", response_model=TripResponse)
def stop_trip(
    id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    trip_service = TripService(db)
    trip = trip_service.stop_trip(user=current_user, trip_id=id)
    return TripResponse.model_validate(trip)
