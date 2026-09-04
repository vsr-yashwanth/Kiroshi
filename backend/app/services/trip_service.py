from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from backend.app.core.errors import (
    EntityNotFoundError,
    AuthorizationError,
    InvalidStateTransitionError,
)
from backend.app.domain.models.user import User
from backend.app.domain.models.trip import Trip
from backend.app.domain.models.itinerary import Itinerary
from backend.app.domain.models.enums import UserRole, TripStatus, EmergencyStatus
from backend.app.repositories.trip_repository import TripRepository
from backend.app.schemas.trip import TripCreate, TripUpdate


class TripService:
    def __init__(self, db: Session):
        self.db = db
        self.trip_repo = TripRepository(db)

    def create_trip(self, user: User, trip_in: TripCreate) -> Trip:
        trip = Trip(
            tourist_id=user.id,
            title=trip_in.title.strip(),
            description=trip_in.description.strip() if trip_in.description else None,
            start_date=trip_in.start_date,
            end_date=trip_in.end_date,
            status=TripStatus.PLANNED,
            emergency_status=EmergencyStatus.NORMAL,
        )
        created_trip = self.trip_repo.create(trip)

        # Create sequential itineraries
        if trip_in.itineraries:
            for idx, item in enumerate(trip_in.itineraries):
                itinerary = Itinerary(
                    trip_id=created_trip.id,
                    destination_name=item.destination_name.strip(),
                    planned_arrival=item.planned_arrival,
                    planned_departure=item.planned_departure,
                    latitude=item.latitude,
                    longitude=item.longitude,
                    sequence_order=item.sequence_order or (idx + 1),
                )
                self.trip_repo.add_itinerary(itinerary)

        return self.trip_repo.get_with_relations(created_trip.id)

    def get_trip(self, user: User, trip_id: UUID) -> Trip:
        trip = self.trip_repo.get_with_relations(trip_id)
        if not trip:
            raise EntityNotFoundError("Trip", trip_id)

        # Authorization check: Tourist must own trip; Authority/Admin can inspect any trip
        if user.role == UserRole.TOURIST and trip.tourist_id != user.id:
            raise AuthorizationError("You are not authorized to view this trip")

        return trip

    def list_trips(
        self,
        user: User,
        status: Optional[TripStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Trip]:
        if user.role == UserRole.TOURIST:
            return self.trip_repo.get_by_tourist_id(
                tourist_id=user.id,
                status=status,
                skip=skip,
                limit=limit,
            )
        else:
            # Authorities, Responders, Admins see all trips
            return self.trip_repo.get_all_trips(
                status=status,
                skip=skip,
                limit=limit,
            )

    def update_trip(self, user: User, trip_id: UUID, trip_in: TripUpdate) -> Trip:
        trip = self.get_trip(user, trip_id)

        if user.role == UserRole.TOURIST and trip.tourist_id != user.id:
            raise AuthorizationError("You cannot modify another user's trip")

        update_dict = trip_in.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(trip, field, value)

        return self.trip_repo.update(trip)

    def start_trip(self, user: User, trip_id: UUID) -> Trip:
        trip = self.get_trip(user, trip_id)

        if user.role == UserRole.TOURIST and trip.tourist_id != user.id:
            raise AuthorizationError("Only the trip owner can start this trip")

        if trip.status != TripStatus.PLANNED:
            raise InvalidStateTransitionError(
                current_state=trip.status.value,
                attempted_state=TripStatus.ACTIVE.value,
            )

        trip.status = TripStatus.ACTIVE
        return self.trip_repo.update(trip)

    def stop_trip(self, user: User, trip_id: UUID) -> Trip:
        trip = self.get_trip(user, trip_id)

        # Allow owner or Authority/Admin to stop an active trip
        if user.role == UserRole.TOURIST and trip.tourist_id != user.id:
            raise AuthorizationError("You are not authorized to conclude this trip")

        if trip.status != TripStatus.ACTIVE:
            raise InvalidStateTransitionError(
                current_state=trip.status.value,
                attempted_state=TripStatus.COMPLETED.value,
            )

        trip.status = TripStatus.COMPLETED
        return self.trip_repo.update(trip)
