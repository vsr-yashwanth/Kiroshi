import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.domain.models.risk_assessment import RiskAssessment
from backend.app.repositories.base import BaseRepository


class RiskRepository(BaseRepository[RiskAssessment]):
    def __init__(self, db: Session):
        super().__init__(RiskAssessment, db)

    def get_latest_for_tourist(self, tourist_id: uuid.UUID) -> Optional[RiskAssessment]:
        return (
            self.db.query(RiskAssessment)
            .filter(RiskAssessment.tourist_id == tourist_id)
            .order_by(desc(RiskAssessment.created_at))
            .first()
        )

    def get_latest_for_trip(self, trip_id: uuid.UUID) -> Optional[RiskAssessment]:
        return (
            self.db.query(RiskAssessment)
            .filter(RiskAssessment.trip_id == trip_id)
            .order_by(desc(RiskAssessment.created_at))
            .first()
        )

    def get_history_for_trip(self, trip_id: uuid.UUID, limit: int = 100) -> List[RiskAssessment]:
        return (
            self.db.query(RiskAssessment)
            .filter(RiskAssessment.trip_id == trip_id)
            .order_by(desc(RiskAssessment.created_at))
            .limit(limit)
            .all()
        )

    def get_history_for_tourist(self, tourist_id: uuid.UUID, limit: int = 100) -> List[RiskAssessment]:
        return (
            self.db.query(RiskAssessment)
            .filter(RiskAssessment.tourist_id == tourist_id)
            .order_by(desc(RiskAssessment.created_at))
            .limit(limit)
            .all()
        )
