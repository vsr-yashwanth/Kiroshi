import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from backend.app.domain.models.location_event import LocationEvent
from backend.app.repositories.base import BaseRepository


class LocationRepository(BaseRepository[LocationEvent]):
    def __init__(self, db: Session):
        super().__init__(LocationEvent, db)

    def get_latest_for_tourist(self, tourist_id: uuid.UUID) -> Optional[LocationEvent]:
        stmt = (
            select(LocationEvent)
            .where(LocationEvent.tourist_id == tourist_id)
            .order_by(desc(LocationEvent.recorded_at))
            .limit(1)
        )
        return self.db.execute(stmt).scalars().first()

    def get_latest_for_trip(self, trip_id: uuid.UUID) -> Optional[LocationEvent]:
        stmt = (
            select(LocationEvent)
            .where(LocationEvent.trip_id == trip_id)
            .order_by(desc(LocationEvent.recorded_at))
            .limit(1)
        )
        return self.db.execute(stmt).scalars().first()

    def get_history_for_trip(self, trip_id: uuid.UUID, limit: int = 500) -> List[LocationEvent]:
        stmt = (
            select(LocationEvent)
            .where(LocationEvent.trip_id == trip_id)
            .order_by(LocationEvent.recorded_at.asc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_active_tourists_latest(self) -> List[LocationEvent]:
        """Returns the latest location event for each tourist who has recorded locations."""
        subquery = (
            select(
                LocationEvent.tourist_id,
                LocationEvent.id,
            )
            .order_by(LocationEvent.tourist_id, desc(LocationEvent.recorded_at))
            .distinct(LocationEvent.tourist_id)
            .subquery()
        )
        # Note: SQLite does not support SELECT DISTINCT ON, so let's write a dialect-safe query
        # Fetch all distinct tourist_ids and their latest location
        tourist_ids = self.db.execute(select(LocationEvent.tourist_id).distinct()).scalars().all()
        results = []
        for tid in tourist_ids:
            latest = self.get_latest_for_tourist(tid)
            if latest:
                results.append(latest)
        return results
