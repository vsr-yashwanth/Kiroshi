import json
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.domain.models.user import User
from backend.app.domain.models.geo_zone import GeoZone
from backend.app.domain.models.enums import UserRole
from backend.app.api.deps import get_current_user, require_role
from backend.app.schemas.zone import GeoZoneCreate, GeoZoneResponse, ZoneEventResponse
from backend.app.repositories.zone_repository import ZoneRepository
from backend.app.services.geospatial_service import GeospatialService

router = APIRouter()


def _format_zone_response(zone: GeoZone) -> GeoZoneResponse:
    coords = json.loads(zone.coordinates_json)
    return GeoZoneResponse(
        id=zone.id,
        name=zone.name,
        description=zone.description,
        zone_type=zone.zone_type,
        coordinates=coords,
        is_active=zone.is_active,
        created_at=zone.created_at,
        updated_at=zone.updated_at,
    )


@router.get(
    "",
    response_model=List[GeoZoneResponse],
    summary="List active GeoZones",
    description="Returns all active monitored safety, restricted, and high-risk zones.",
)
def list_zones(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = ZoneRepository(db)
    zones = repo.list_active()
    return [_format_zone_response(z) for z in zones]


@router.post(
    "",
    response_model=GeoZoneResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new GeoZone",
    description="Creates a spatial polygon boundary with specified zone type (SAFE, RESTRICTED, HIGH_RISK, CUSTOM).",
)
def create_zone(
    payload: GeoZoneCreate,
    current_user: User = Depends(require_role(UserRole.AUTHORITY, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    repo = ZoneRepository(db)
    existing = repo.get_by_name(payload.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A GeoZone with the name '{payload.name}' already exists.",
        )

    try:
        geom_wkt, coords_json = GeospatialService.create_polygon_wkt(payload.coordinates)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    zone = GeoZone(
        name=payload.name,
        description=payload.description,
        zone_type=payload.zone_type,
        geom=geom_wkt,
        coordinates_json=coords_json,
        is_active=True,
    )
    saved_zone = repo.create(zone)
    return _format_zone_response(saved_zone)


@router.get(
    "/events",
    response_model=List[ZoneEventResponse],
    summary="List recent GeoZone ENTER/EXIT transition events",
    description="Returns historical audit log of tourists entering and exiting safety zones.",
)
def list_zone_events(
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: User = Depends(require_role(UserRole.AUTHORITY, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    repo = ZoneRepository(db)
    events = repo.list_recent_events(limit=limit)
    results = []
    for e in events:
        results.append(
            ZoneEventResponse(
                id=e.id,
                tourist_id=e.tourist_id,
                trip_id=e.trip_id,
                zone_id=e.zone_id,
                zone_name=e.zone.name if e.zone else None,
                zone_type=e.zone.zone_type if e.zone else None,
                event_type=e.event_type,
                location_event_id=e.location_event_id,
                occurred_at=e.occurred_at,
            )
        )
    return results


@router.get(
    "/{id}",
    response_model=GeoZoneResponse,
    summary="Get GeoZone details",
)
def get_zone(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = ZoneRepository(db)
    zone = repo.get(id)
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GeoZone not found.")
    return _format_zone_response(zone)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate or delete a GeoZone",
)
def delete_zone(
    id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.AUTHORITY, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    repo = ZoneRepository(db)
    zone = repo.get(id)
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GeoZone not found.")
    repo.delete(id)
    return None
