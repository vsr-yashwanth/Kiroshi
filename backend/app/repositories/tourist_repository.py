from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from backend.app.domain.models.tourist_profile import TouristProfile
from backend.app.domain.models.user import User
from backend.app.domain.models.enums import UserRole
from backend.app.repositories.base import BaseRepository


class TouristRepository(BaseRepository[TouristProfile]):
    def __init__(self, db: Session):
        super().__init__(TouristProfile, db)

    def get_by_user_id(self, user_id: UUID) -> Optional[TouristProfile]:
        return (
            self.db.query(TouristProfile)
            .options(joinedload(TouristProfile.user))
            .filter(TouristProfile.user_id == user_id)
            .first()
        )

    def get_with_user(self, profile_id: UUID) -> Optional[TouristProfile]:
        return (
            self.db.query(TouristProfile)
            .options(joinedload(TouristProfile.user))
            .filter(TouristProfile.id == profile_id)
            .first()
        )

    def get_all_tourist_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        return (
            self.db.query(User)
            .options(joinedload(User.tourist_profile))
            .filter(User.role == UserRole.TOURIST)
            .offset(skip)
            .limit(limit)
            .all()
        )
