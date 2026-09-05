import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.app.core.logging import logger
from backend.app.domain.models.user import User
from backend.app.domain.models.trip import Trip
from backend.app.domain.models.enums import (
    SyncEventType,
    SyncEventStatus,
    TripStatus,
    IncidentStatus,
)
from backend.app.domain.models.sync_record import SyncRecord
from backend.app.schemas.sync import (
    SyncBatchRequest,
    SyncBatchResponse,
    SyncEventItem,
    SyncEventResult,
)
from backend.app.schemas.location import LocationIngestRequest
from backend.app.repositories.sync_repository import SyncRepository
from backend.app.repositories.trip_repository import TripRepository
from backend.app.repositories.incident_repository import IncidentRepository
from backend.app.services.incident_service import IncidentService
from backend.app.services.location_service import LocationService
from backend.app.services.trip_service import TripService


class SyncService:
    def __init__(self, db: Session):
        self.db = db
        self.sync_repo = SyncRepository(db)
        self.trip_repo = TripRepository(db)
        self.incident_repo = IncidentRepository(db)
        self.incident_service = IncidentService(db)
        self.location_service = LocationService(db)
        self.trip_service = TripService(db)

    async def process_batch(
        self, current_user: User, batch: SyncBatchRequest
    ) -> SyncBatchResponse:
        """
        Synchronizes a batch of offline events with strict server-side idempotency,
        partial batch tolerance, and deterministic conflict resolution.
        """
        # 1. Sort events chronologically to preserve intent and state ordering
        sorted_events = sorted(batch.events, key=lambda ev: ev.timestamp)

        results: List[SyncEventResult] = []
        synced_count = 0
        duplicate_count = 0
        failed_count = 0

        for event in sorted_events:
            now_utc = datetime.now(timezone.utc)

            # 2. Check Idempotency Record (Fast duplicate suppression)
            existing_record = self.sync_repo.get_by_idempotency_key(event.local_event_id)
            if existing_record:
                logger.info(
                    f"Sync duplicate suppressed for key={event.local_event_id} "
                    f"type={event.event_type} user={current_user.id}"
                )
                results.append(
                    SyncEventResult(
                        local_event_id=event.local_event_id,
                        status=SyncEventStatus.DUPLICATE,
                        server_id=existing_record.resource_id,
                        message="Event already synchronized and processed.",
                        server_timestamp=now_utc,
                        conflict_details={
                            "original_sync_time": existing_record.created_at.isoformat(),
                            "resource_type": existing_record.resource_type,
                        },
                    )
                )
                duplicate_count += 1
                continue

            # 3. Process Individual Event
            try:
                result = await self._process_single_event(
                    current_user=current_user,
                    event=event,
                    now_utc=now_utc,
                )


                results.append(result)
                if result.status in (SyncEventStatus.SYNCED, SyncEventStatus.DUPLICATE):
                    if result.status == SyncEventStatus.SYNCED:
                        synced_count += 1
                    else:
                        duplicate_count += 1
                else:
                    failed_count += 1

            except HTTPException as http_exc:
                self.db.rollback()
                logger.warning(
                    f"Sync item failed: key={event.local_event_id} "
                    f"status={http_exc.status_code} detail={http_exc.detail}"
                )
                results.append(
                    SyncEventResult(
                        local_event_id=event.local_event_id,
                        status=SyncEventStatus.REJECTED,
                        message=str(http_exc.detail),
                        server_timestamp=now_utc,
                    )
                )
                failed_count += 1
            except Exception as exc:
                self.db.rollback()
                logger.error(
                    f"Unexpected error processing sync key={event.local_event_id}: {exc}",
                    exc_info=True,
                )
                results.append(
                    SyncEventResult(
                        local_event_id=event.local_event_id,
                        status=SyncEventStatus.ERROR,
                        message=f"Server error during event synchronization: {str(exc)}",
                        server_timestamp=now_utc,
                    )
                )
                failed_count += 1

        return SyncBatchResponse(
            results=results,
            synced_count=synced_count,
            duplicate_count=duplicate_count,
            failed_count=failed_count,
        )

    async def _process_single_event(
        self, current_user: User, event: SyncEventItem, now_utc: datetime
    ) -> SyncEventResult:
        if event.event_type == SyncEventType.SOS_EVENT:
            return await self._handle_sos_event(current_user, event, now_utc)
        elif event.event_type == SyncEventType.LOCATION_EVENT:
            return await self._handle_location_event(current_user, event, now_utc)
        elif event.event_type == SyncEventType.TRIP_UPDATE:
            return self._handle_trip_update(current_user, event, now_utc)
        elif event.event_type == SyncEventType.INCIDENT_ACTION:
            return await self._handle_incident_action(current_user, event, now_utc)
        else:
            return SyncEventResult(
                local_event_id=event.local_event_id,
                status=SyncEventStatus.REJECTED,
                message=f"Unsupported sync event type: {event.event_type}",
                server_timestamp=now_utc,
            )

    async def _handle_sos_event(
        self, current_user: User, event: SyncEventItem, now_utc: datetime
    ) -> SyncEventResult:
        payload = event.payload
        raw_trip_id = payload.get("trip_id")
        trip_uuid = uuid.UUID(raw_trip_id) if raw_trip_id else None

        # Delegate to IncidentService which enforces role, location fallback, and incident persistence
        incident = await self.incident_service.create_sos(
            current_user=current_user,
            trip_id=trip_uuid,
            latitude=payload.get("latitude"),
            longitude=payload.get("longitude"),
            accuracy=payload.get("accuracy"),
            description=payload.get("notes") or payload.get("description"),
            idempotency_key=event.local_event_id,
        )

        # Audit sync record
        record = SyncRecord(
            user_id=current_user.id,
            idempotency_key=event.local_event_id,
            event_type=SyncEventType.SOS_EVENT,
            resource_type="incidents",
            resource_id=incident.id,
            status=SyncEventStatus.SYNCED,
            response_payload={
                "incident_id": str(incident.id),
                "severity": incident.severity.value,
                "status": incident.status.value,
            },
        )
        self.sync_repo.create(record)

        return SyncEventResult(
            local_event_id=event.local_event_id,
            status=SyncEventStatus.SYNCED,
            server_id=incident.id,
            message="Emergency SOS successfully synchronized and authoritative incident created.",
            server_timestamp=now_utc,
        )

    async def _handle_location_event(
        self, current_user: User, event: SyncEventItem, now_utc: datetime
    ) -> SyncEventResult:
        payload = event.payload
        raw_trip_id = payload.get("trip_id")
        if not raw_trip_id:
            return SyncEventResult(
                local_event_id=event.local_event_id,
                status=SyncEventStatus.REJECTED,
                message="Missing trip_id in location event payload.",
                server_timestamp=now_utc,
            )

        trip_uuid = uuid.UUID(raw_trip_id)
        trip = self.trip_repo.get(trip_uuid)
        if not trip or trip.tourist_id != current_user.id:
            return SyncEventResult(
                local_event_id=event.local_event_id,
                status=SyncEventStatus.REJECTED,
                message="Trip not found or unauthorized.",
                server_timestamp=now_utc,
            )

        # Conflict check: If trip was completed on server while client was offline
        if trip.status != TripStatus.ACTIVE:
            return SyncEventResult(
                local_event_id=event.local_event_id,
                status=SyncEventStatus.CONFLICT,
                message=f"Cannot synchronize location: Trip is currently '{trip.status.value}' on server.",
                server_timestamp=now_utc,
                conflict_details={
                    "trip_id": str(trip.id),
                    "server_trip_status": trip.status.value,
                    "resolution": "SERVER_WINS",
                },
            )

        raw_rec_at = payload.get("recorded_at") or event.timestamp
        if isinstance(raw_rec_at, str):
            rec_at = datetime.fromisoformat(raw_rec_at.replace("Z", "+00:00"))
        else:
            rec_at = raw_rec_at

        loc_request = LocationIngestRequest(
            trip_id=trip_uuid,
            latitude=payload.get("latitude"),
            longitude=payload.get("longitude"),
            accuracy=payload.get("accuracy", 10.0),
            altitude=payload.get("altitude"),
            speed=payload.get("speed"),
            heading=payload.get("heading"),
            recorded_at=rec_at,
        )

        loc_response = await self.location_service.ingest_location(
            current_user=current_user,
            payload=loc_request,
        )

        # Audit sync record
        record = SyncRecord(
            user_id=current_user.id,
            idempotency_key=event.local_event_id,
            event_type=SyncEventType.LOCATION_EVENT,
            resource_type="location_events",
            resource_id=loc_response.id,
            status=SyncEventStatus.SYNCED,
            response_payload={
                "location_event_id": str(loc_response.id),
                "freshness": loc_response.freshness.value,
                "risk_level": loc_response.risk_level,
            },
        )
        self.sync_repo.create(record)

        return SyncEventResult(
            local_event_id=event.local_event_id,
            status=SyncEventStatus.SYNCED,
            server_id=loc_response.id,
            message="Location breadcrumb successfully ingested and evaluated.",
            server_timestamp=now_utc,
        )

    def _handle_trip_update(
        self, current_user: User, event: SyncEventItem, now_utc: datetime
    ) -> SyncEventResult:
        payload = event.payload
        action = (payload.get("action") or "").upper()
        raw_trip_id = payload.get("trip_id")
        if not raw_trip_id:
            return SyncEventResult(
                local_event_id=event.local_event_id,
                status=SyncEventStatus.REJECTED,
                message="Missing trip_id in trip update payload.",
                server_timestamp=now_utc,
            )

        trip_uuid = uuid.UUID(raw_trip_id)
        trip = self.trip_repo.get(trip_uuid)
        if not trip:
            return SyncEventResult(
                local_event_id=event.local_event_id,
                status=SyncEventStatus.REJECTED,
                message=f"Trip {trip_uuid} not found.",
                server_timestamp=now_utc,
            )

        if action == "START":
            if trip.status == TripStatus.ACTIVE:
                # Idempotent success: already active
                return SyncEventResult(
                    local_event_id=event.local_event_id,
                    status=SyncEventStatus.SYNCED,
                    server_id=trip.id,
                    message="Trip is already active on server.",
                    server_timestamp=now_utc,
                )
            elif trip.status in (TripStatus.COMPLETED, TripStatus.CANCELLED):
                # Conflict: cannot restart completed trip
                return SyncEventResult(
                    local_event_id=event.local_event_id,
                    status=SyncEventStatus.CONFLICT,
                    server_id=trip.id,
                    message=f"Conflict: Trip is already '{trip.status.value}' on server.",
                    server_timestamp=now_utc,
                    conflict_details={
                        "server_status": trip.status.value,
                        "resolution": "SERVER_WINS",
                    },
                )
            else:
                updated_trip = self.trip_service.start_trip(current_user, trip_uuid)
                record = SyncRecord(
                    user_id=current_user.id,
                    idempotency_key=event.local_event_id,
                    event_type=SyncEventType.TRIP_UPDATE,
                    resource_type="trips",
                    resource_id=updated_trip.id,
                    status=SyncEventStatus.SYNCED,
                    response_payload={"status": updated_trip.status.value},
                )
                self.sync_repo.create(record)
                return SyncEventResult(
                    local_event_id=event.local_event_id,
                    status=SyncEventStatus.SYNCED,
                    server_id=updated_trip.id,
                    message="Trip started successfully.",
                    server_timestamp=now_utc,
                )

        elif action == "STOP":
            if trip.status == TripStatus.COMPLETED:
                # Idempotent success: already completed
                return SyncEventResult(
                    local_event_id=event.local_event_id,
                    status=SyncEventStatus.SYNCED,
                    server_id=trip.id,
                    message="Trip is already completed on server.",
                    server_timestamp=now_utc,
                )
            elif trip.status != TripStatus.ACTIVE:
                return SyncEventResult(
                    local_event_id=event.local_event_id,
                    status=SyncEventStatus.CONFLICT,
                    server_id=trip.id,
                    message=f"Cannot stop trip in '{trip.status.value}' state.",
                    server_timestamp=now_utc,
                    conflict_details={
                        "server_status": trip.status.value,
                        "resolution": "SERVER_WINS",
                    },
                )
            else:
                updated_trip = self.trip_service.stop_trip(current_user, trip_uuid)
                record = SyncRecord(
                    user_id=current_user.id,
                    idempotency_key=event.local_event_id,
                    event_type=SyncEventType.TRIP_UPDATE,
                    resource_type="trips",
                    resource_id=updated_trip.id,
                    status=SyncEventStatus.SYNCED,
                    response_payload={"status": updated_trip.status.value},
                )
                self.sync_repo.create(record)
                return SyncEventResult(
                    local_event_id=event.local_event_id,
                    status=SyncEventStatus.SYNCED,
                    server_id=updated_trip.id,
                    message="Trip stopped successfully.",
                    server_timestamp=now_utc,
                )
        else:
            return SyncEventResult(
                local_event_id=event.local_event_id,
                status=SyncEventStatus.REJECTED,
                message=f"Unsupported trip action: '{action}'",
                server_timestamp=now_utc,
            )

    async def _handle_incident_action(
        self, current_user: User, event: SyncEventItem, now_utc: datetime
    ) -> SyncEventResult:
        payload = event.payload
        raw_incident_id = payload.get("incident_id")
        if not raw_incident_id:
            return SyncEventResult(
                local_event_id=event.local_event_id,
                status=SyncEventStatus.REJECTED,
                message="Missing incident_id in incident action payload.",
                server_timestamp=now_utc,
            )

        incident_uuid = uuid.UUID(raw_incident_id)
        incident = self.incident_repo.get(incident_uuid)
        if not incident:
            return SyncEventResult(
                local_event_id=event.local_event_id,
                status=SyncEventStatus.REJECTED,
                message=f"Incident {incident_uuid} not found.",
                server_timestamp=now_utc,
            )

        to_status_str = payload.get("to_status")
        try:
            to_status = IncidentStatus(to_status_str)
        except (ValueError, TypeError):
            return SyncEventResult(
                local_event_id=event.local_event_id,
                status=SyncEventStatus.REJECTED,
                message=f"Invalid to_status: '{to_status_str}'",
                server_timestamp=now_utc,
            )

        # Check if already at desired status
        if incident.status == to_status:
            return SyncEventResult(
                local_event_id=event.local_event_id,
                status=SyncEventStatus.SYNCED,
                server_id=incident.id,
                message=f"Incident is already at status '{to_status.value}'.",
                server_timestamp=now_utc,
            )

        try:
            updated_incident = await self.incident_service.transition_incident(
                incident_id=incident_uuid,
                to_status=to_status,
                actor=current_user,
                reason=payload.get("reason"),
                resolution_notes=payload.get("resolution_notes"),
            )
            record = SyncRecord(
                user_id=current_user.id,
                idempotency_key=event.local_event_id,
                event_type=SyncEventType.INCIDENT_ACTION,
                resource_type="incidents",
                resource_id=updated_incident.id,
                status=SyncEventStatus.SYNCED,
                response_payload={"status": updated_incident.status.value},
            )
            self.sync_repo.create(record)
            return SyncEventResult(
                local_event_id=event.local_event_id,
                status=SyncEventStatus.SYNCED,
                server_id=updated_incident.id,
                message=f"Incident transitioned to {to_status.value}.",
                server_timestamp=now_utc,
            )
        except HTTPException as he:
            # Detect state conflict
            return SyncEventResult(
                local_event_id=event.local_event_id,
                status=SyncEventStatus.CONFLICT,
                server_id=incident.id,
                message=f"Incident state transition conflict: {he.detail}",
                server_timestamp=now_utc,
                conflict_details={
                    "current_server_status": incident.status.value,
                    "attempted_status": to_status.value,
                    "resolution": "SERVER_WINS",
                },
            )
