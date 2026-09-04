import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.domain.models.user import User
from backend.app.domain.models.enums import UserRole
from backend.app.api.deps import get_current_user, require_role
from backend.app.schemas.risk import (
    RiskAssessmentResponse,
    LiveTouristRiskSnapshot,
)
from backend.app.services.risk_service import RiskService

router = APIRouter()


@router.get(
    "/current/{tourist_id}",
    response_model=Optional[RiskAssessmentResponse],
    summary="Get current risk assessment for a tourist",
    description="Returns the most recent explainable risk assessment for a tourist. Accessible by the tourist themselves or authorities.",
)
def get_current_risk(
    tourist_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = RiskService(db)
    assessment = service.get_current_risk_for_tourist(current_user=current_user, tourist_id=tourist_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No risk assessment found for tourist {tourist_id}.",
        )
    return assessment


@router.get(
    "/history/{trip_id}",
    response_model=List[RiskAssessmentResponse],
    summary="Get risk evaluation history for a trip",
    description="Returns the chronological evaluation history of risk scores, signals, and explanations for an active or completed trip.",
)
def get_trip_risk_history(
    trip_id: uuid.UUID,
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = RiskService(db)
    return service.get_trip_risk_history(current_user=current_user, trip_id=trip_id, limit=limit)


@router.get(
    "/active",
    response_model=List[LiveTouristRiskSnapshot],
    summary="Get active tourists risk snapshot",
    description="Authority endpoint returning the latest risk evaluation, score, level, and explanation across all active trips.",
)
def get_active_tourists_risk_snapshot(
    current_user: User = Depends(require_role(UserRole.AUTHORITY, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    service = RiskService(db)
    return service.get_active_tourists_risk_snapshot(current_user=current_user)
