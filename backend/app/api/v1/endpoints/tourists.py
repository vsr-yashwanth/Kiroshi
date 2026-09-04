from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_active_user, require_role
from backend.app.domain.models.user import User
from backend.app.domain.models.enums import UserRole
from backend.app.services.tourist_service import TouristService
from backend.app.schemas.tourist import TouristProfileUpdate, TouristProfileResponse
from backend.app.schemas.auth import UserResponse

router = APIRouter()


@router.get("/me", response_model=TouristProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    tourist_service = TouristService(db)
    profile = tourist_service.get_own_profile(current_user)
    return TouristProfileResponse.model_validate(profile)


@router.put("/me", response_model=TouristProfileResponse)
def update_my_profile(
    update_data: TouristProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    tourist_service = TouristService(db)
    profile = tourist_service.update_own_profile(current_user, update_data)
    return TouristProfileResponse.model_validate(profile)


@router.get("", response_model=List[UserResponse])
def list_tourists(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role(UserRole.AUTHORITY, UserRole.ADMIN, UserRole.RESPONDER)),
    db: Session = Depends(get_db),
):
    tourist_service = TouristService(db)
    users = tourist_service.list_tourists_for_authority(current_user, skip=skip, limit=limit)
    return [UserResponse.model_validate(u) for u in users]


@router.get("/{id}", response_model=TouristProfileResponse)
def get_tourist_profile_by_id(
    id: UUID,
    current_user: User = Depends(require_role(UserRole.AUTHORITY, UserRole.ADMIN, UserRole.RESPONDER)),
    db: Session = Depends(get_db),
):
    tourist_service = TouristService(db)
    profile = tourist_service.get_tourist_by_id_for_authority(current_user, id)
    return TouristProfileResponse.model_validate(profile)
