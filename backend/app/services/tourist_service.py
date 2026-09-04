from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from backend.app.core.errors import EntityNotFoundError, AuthorizationError
from backend.app.domain.models.user import User
from backend.app.domain.models.tourist_profile import TouristProfile
from backend.app.domain.models.enums import UserRole
from backend.app.repositories.tourist_repository import TouristRepository
from backend.app.repositories.user_repository import UserRepository
from backend.app.schemas.tourist import TouristProfileUpdate


class TouristService:
    def __init__(self, db: Session):
        self.db = db
        self.tourist_repo = TouristRepository(db)
        self.user_repo = UserRepository(db)

    def get_own_profile(self, user: User) -> TouristProfile:
        profile = self.tourist_repo.get_by_user_id(user.id)
        if not profile:
            # Create default profile if missing
            profile = TouristProfile(user_id=user.id)
            profile = self.tourist_repo.create(profile)
        return profile

    def update_own_profile(self, user: User, update_data: TouristProfileUpdate) -> TouristProfile:
        profile = self.get_own_profile(user)
        update_dict = update_data.model_dump(exclude_unset=True)

        for key, value in update_dict.items():
            setattr(profile, key, value)

        return self.tourist_repo.update(profile)

    def get_tourist_by_id_for_authority(self, requesting_user: User, user_id: UUID) -> TouristProfile:
        if requesting_user.role not in [UserRole.AUTHORITY, UserRole.ADMIN, UserRole.RESPONDER]:
            raise AuthorizationError("Only authorities and responders can inspect other tourist profiles")

        profile = self.tourist_repo.get_by_user_id(user_id)
        if not profile:
            raise EntityNotFoundError("TouristProfile", user_id)
        return profile

    def list_tourists_for_authority(self, requesting_user: User, skip: int = 0, limit: int = 100) -> List[User]:
        if requesting_user.role not in [UserRole.AUTHORITY, UserRole.ADMIN, UserRole.RESPONDER]:
            raise AuthorizationError("Only authorities can list tourists")

        return self.tourist_repo.get_all_tourist_users(skip=skip, limit=limit)
