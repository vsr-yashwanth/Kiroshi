from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from backend.app.core.errors import EntityNotFoundError, AuthorizationError
from backend.app.domain.models.user import User
from backend.app.domain.models.tourist_profile import TouristProfile
from backend.app.domain.models.enums import UserRole, AuditEventType, AuditOutcome
from backend.app.repositories.tourist_repository import TouristRepository
from backend.app.repositories.user_repository import UserRepository
from backend.app.repositories.audit_repository import AuditRepository
from backend.app.schemas.tourist import TouristProfileUpdate


class TouristService:
    def __init__(self, db: Session):
        self.db = db
        self.tourist_repo = TouristRepository(db)
        self.user_repo = UserRepository(db)
        self.audit_repo = AuditRepository(db)

    def get_own_profile(self, user: User) -> TouristProfile:
        profile = self.tourist_repo.get_by_user_id(user.id)
        if not profile:
            # Create default profile if missing
            profile = TouristProfile(user_id=user.id)
            profile = self.tourist_repo.create(profile)

        self.audit_repo.create_event(
            event_type=AuditEventType.PROFILE_READ,
            action="READ_OWN",
            resource_type="TOURIST_PROFILE",
            resource_id=str(profile.id),
            actor_id=user.id,
            actor_email=user.email,
            actor_role=user.role.value,
            outcome=AuditOutcome.SUCCESS,
            details={"consent_given": profile.consent_given},
        )
        return profile

    def update_own_profile(self, user: User, update_data: TouristProfileUpdate) -> TouristProfile:
        profile = self.get_own_profile(user)
        update_dict = update_data.model_dump(exclude_unset=True)

        consent_changed = "consent_given" in update_dict and update_dict["consent_given"] != profile.consent_given
        old_consent = profile.consent_given

        for key, value in update_dict.items():
            setattr(profile, key, value)

        updated_profile = self.tourist_repo.update(profile)

        if consent_changed:
            self.audit_repo.create_event(
                event_type=AuditEventType.PROFILE_CONSENT_CHANGE,
                action="UPDATE_CONSENT",
                resource_type="TOURIST_PROFILE",
                resource_id=str(updated_profile.id),
                actor_id=user.id,
                actor_email=user.email,
                actor_role=user.role.value,
                outcome=AuditOutcome.SUCCESS,
                details={"from_consent": old_consent, "to_consent": updated_profile.consent_given},
            )
        else:
            self.audit_repo.create_event(
                event_type=AuditEventType.PROFILE_UPDATE,
                action="UPDATE_PROFILE",
                resource_type="TOURIST_PROFILE",
                resource_id=str(updated_profile.id),
                actor_id=user.id,
                actor_email=user.email,
                actor_role=user.role.value,
                outcome=AuditOutcome.SUCCESS,
                details={"updated_fields": list(update_dict.keys())},
            )

        return updated_profile

    def get_tourist_by_id_for_authority(self, requesting_user: User, user_id: UUID) -> TouristProfile:
        if requesting_user.role not in [UserRole.AUTHORITY, UserRole.ADMIN, UserRole.RESPONDER]:
            self.audit_repo.create_event(
                event_type=AuditEventType.PROFILE_READ,
                action="READ_REMOTE",
                resource_type="TOURIST_PROFILE",
                resource_id=str(user_id),
                actor_id=requesting_user.id,
                actor_email=requesting_user.email,
                actor_role=requesting_user.role.value,
                outcome=AuditOutcome.DENIED,
                details={"reason": "Insufficient role"},
            )
            raise AuthorizationError("Only authorities and responders can inspect other tourist profiles")

        profile = self.tourist_repo.get_by_user_id(user_id)
        if not profile:
            raise EntityNotFoundError("TouristProfile", user_id)

        self.audit_repo.create_event(
            event_type=AuditEventType.PROFILE_READ,
            action="READ_REMOTE",
            resource_type="TOURIST_PROFILE",
            resource_id=str(profile.id),
            actor_id=requesting_user.id,
            actor_email=requesting_user.email,
            actor_role=requesting_user.role.value,
            outcome=AuditOutcome.SUCCESS,
            details={"target_tourist_user_id": str(user_id)},
        )
        return profile

    def list_tourists_for_authority(self, requesting_user: User, skip: int = 0, limit: int = 100) -> List[User]:
        if requesting_user.role not in [UserRole.AUTHORITY, UserRole.ADMIN, UserRole.RESPONDER]:
            raise AuthorizationError("Only authorities can list tourists")

        users = self.tourist_repo.get_all_tourist_users(skip=skip, limit=limit)
        self.audit_repo.create_event(
            event_type=AuditEventType.PROFILE_READ,
            action="LIST_PROFILES",
            resource_type="TOURIST_USERS",
            resource_id=None,
            actor_id=requesting_user.id,
            actor_email=requesting_user.email,
            actor_role=requesting_user.role.value,
            outcome=AuditOutcome.SUCCESS,
            details={"skip": skip, "limit": limit, "count_returned": len(users)},
        )
        return users
