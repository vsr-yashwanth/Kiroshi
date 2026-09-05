from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from backend.app.domain.models.sync_record import SyncRecord
from backend.app.repositories.base import BaseRepository


class SyncRepository(BaseRepository[SyncRecord]):
    def __init__(self, db: Session):
        super().__init__(SyncRecord, db)

    def get_by_idempotency_key(self, idempotency_key: str) -> Optional[SyncRecord]:
        return (
            self.db.query(SyncRecord)
            .filter(SyncRecord.idempotency_key == idempotency_key)
            .first()
        )

    def get_by_user_and_key(
        self, user_id: UUID, idempotency_key: str
    ) -> Optional[SyncRecord]:
        return (
            self.db.query(SyncRecord)
            .filter(
                SyncRecord.user_id == user_id,
                SyncRecord.idempotency_key == idempotency_key,
            )
            .first()
        )

    def get_user_sync_records(
        self, user_id: UUID, limit: int = 100
    ) -> List[SyncRecord]:
        return (
            self.db.query(SyncRecord)
            .filter(SyncRecord.user_id == user_id)
            .order_by(SyncRecord.created_at.desc())
            .limit(limit)
            .all()
        )
