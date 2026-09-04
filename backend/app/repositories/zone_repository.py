import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, delete
from backend.app.domain.models.geo_zone import GeoZone
from backend.app.domain.models.zone_event import TouristZoneState, ZoneEvent
from backend.app.repositories.base import BaseRepository


class ZoneRepository(BaseRepository[GeoZone]):
    def __init__(self, db: Session):
        super().__init__(GeoZone, db)

    def get_by_name(self, name: str) -> Optional[GeoZone]:
        stmt = select(GeoZone).where(GeoZone.name == name)
        return self.db.execute(stmt).scalars().first()

    def list_active(self) -> List[GeoZone]:
        stmt = select(GeoZone).where(GeoZone.is_active == True).order_by(GeoZone.name.asc())
        return list(self.db.execute(stmt).scalars().all())

    def get_tourist_current_zones(self, tourist_id: uuid.UUID) -> List[TouristZoneState]:
        stmt = (
            select(TouristZoneState)
            .where(TouristZoneState.tourist_id == tourist_id)
        )
        return list(self.db.execute(stmt).scalars().all())

    def set_tourist_in_zone(self, tourist_id: uuid.UUID, zone_id: uuid.UUID, entered_at: datetime) -> TouristZoneState:
        existing = (
            self.db.execute(
                select(TouristZoneState).where(
                    TouristZoneState.tourist_id == tourist_id,
                    TouristZoneState.zone_id == zone_id,
                )
            )
            .scalars()
            .first()
        )
        if existing:
            existing.last_seen_at = entered_at
            self.db.commit()
            self.db.refresh(existing)
            return existing

        state = TouristZoneState(
            tourist_id=tourist_id,
            zone_id=zone_id,
            entered_at=entered_at,
            last_seen_at=entered_at,
        )
        self.db.add(state)
        self.db.commit()
        self.db.refresh(state)
        return state

    def remove_tourist_from_zone(self, tourist_id: uuid.UUID, zone_id: uuid.UUID) -> bool:
        stmt = delete(TouristZoneState).where(
            TouristZoneState.tourist_id == tourist_id,
            TouristZoneState.zone_id == zone_id,
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0

    def create_zone_event(self, event: ZoneEvent) -> ZoneEvent:
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list_recent_events(self, limit: int = 100) -> List[ZoneEvent]:
        stmt = (
            select(ZoneEvent)
            .order_by(desc(ZoneEvent.occurred_at))
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
