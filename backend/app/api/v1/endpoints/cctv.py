from __future__ import annotations

import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, require_role, require_authority_or_admin
from backend.app.domain.models.enums import UserRole
from backend.app.domain.models.user import User
from backend.app.schemas.cctv import (
    CameraCreate,
    CameraResponse,
    CCTVInvestigationRequest,
    CCTVInvestigationResponse,
)
from backend.app.services.cctv_service import CCTVService

router = APIRouter(prefix="/cctv", tags=["cctv"])


@router.post(
    "/cameras",
    response_model=CameraResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new CCTV camera (Admin/Authority only)",
)
def register_camera(
    data: CameraCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authority_or_admin),
) -> CameraResponse:
    service = CCTVService(db)
    return service.register_camera(data)


@router.get(
    "/cameras/nearby",
    response_model=List[CameraResponse],
    summary="Find active cameras within spatial radius of a location (Authority/Operator/Admin)",
)
def get_nearby_cameras(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    radius_meters: float = Query(200.0, ge=10.0, le=5000.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.AUTHORITY, UserRole.RESPONDER, UserRole.ADMIN)),
) -> List[CameraResponse]:
    service = CCTVService(db)
    return service.find_nearby_cameras(
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters,
    )


@router.post(
    "/investigate",
    response_model=CCTVInvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute a scoped, authorized CCTV investigation on an incident",
)
def investigate_incident(
    data: CCTVInvestigationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authority_or_admin),
) -> CCTVInvestigationResponse:
    service = CCTVService(db)
    return service.run_cctv_investigation(
        request=data,
        requested_by_user_id=current_user.id,
    )


@router.get(
    "/investigations/{investigation_id}",
    response_model=CCTVInvestigationResponse,
    summary="Retrieve CCTV investigation details and audit records",
)
def get_investigation(
    investigation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authority_or_admin),
) -> CCTVInvestigationResponse:
    service = CCTVService(db)
    inv = service.cctv_repo.get_investigation_by_id(investigation_id)
    if not inv:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation {investigation_id} not found."
        )
    return service._to_investigation_response(inv)
