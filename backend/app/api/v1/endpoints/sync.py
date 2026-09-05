from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_active_user
from backend.app.domain.models.user import User
from backend.app.schemas.sync import SyncBatchRequest, SyncBatchResponse
from backend.app.services.sync_service import SyncService

router = APIRouter()


@router.post(
    "/events",
    response_model=SyncBatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Synchronize offline event queue batch",
    description=(
        "Processes an ordered batch of offline queued events (SOS beacons, location telemetry, "
        "trip updates, incident actions) with strict server-side idempotency, partial failure isolation, "
        "and deterministic conflict resolution."
    ),
)
async def synchronize_events(
    payload: SyncBatchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = SyncService(db)
    return await service.process_batch(current_user=current_user, batch=payload)
