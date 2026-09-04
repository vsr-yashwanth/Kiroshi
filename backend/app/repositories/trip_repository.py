from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from backend.app.domain.models.trip import Trip
from backend.app.domain.models.itinerary import Itinerary
from backend.app.domain.models.enums import TripStatus
from backend.app.repositories.base import BaseRepository


class TripRepository(BaseRepository[Trip]):
    def __init__(self, db: Session):
        super().__init__(Trip, db)

    def get_with_relations(self, trip_id: UUID) -> Optional[Trip]:
        return (
            self.db.query(Trip)
            .options(joinedload(Trip.tourist), joinedload(Trip.itineraries))
            .filter(Trip.id == trip_id)
            .first()
        )

    def get_by_tourist_id(
        self,
        tourist_id: UUID,
        status: Optional[TripStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Trip]:
        query = (
            self.db.query(Trip)
            .options(joinedload(Trip.itineraries))
            .filter(Trip.tourist_id == tourist_id)
        )
        if status:
            query = query.filter(Trip.status == status)
        return query.order_by(Trip.created_at.desc()).offset(skip).limit(limit).all()

    def get_all_trips(
        self,
        status: Optional[TripStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Trip]:
        query = (
            self.db.query(Trip)
            .options(joinedload(Trip.tourist), joinedload(Trip.itineraries))
        )
        if status:
            query = query.filter(Trip.status == status)
        return query.order_by(Trip.created_at.desc()).offset(skip).limit(limit).all()

    def add_itinerary(self, itinerary: Itinerary) -> Itinerary:
        self.db.add(itinerary)
        self.db.commit()
        self.db.refresh(itinerary)
        return itinerary
