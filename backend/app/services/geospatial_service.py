import json
import uuid
from datetime import datetime
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from geoalchemy2.elements import WKTElement
import shapely.geometry
import shapely.wkt

from backend.app.core.database import is_sqlite
from backend.app.core.logging import logger
from backend.app.domain.models.geo_zone import GeoZone
from backend.app.domain.models.zone_event import TouristZoneState, ZoneEvent
from backend.app.domain.models.enums import ZoneEventType
from backend.app.repositories.zone_repository import ZoneRepository


class GeospatialService:
    def __init__(self, db: Session):
        self.db = db
        self.zone_repo = ZoneRepository(db)

    @staticmethod
    def create_point_wkt(longitude: float, latitude: float) -> WKTElement:
        pt = shapely.geometry.Point(longitude, latitude)
        return WKTElement(pt.wkt, srid=4326)

    @staticmethod
    def create_polygon_wkt(coordinates: List[List[float]]) -> Tuple[WKTElement, str]:
        """Converts coordinates list [[lng, lat], ...] to WKTElement and JSON string."""
        # Ensure coordinates are (lng, lat) tuples
        shell = [(float(pt[0]), float(pt[1])) for pt in coordinates]
        if shell[0] != shell[-1]:
            shell.append(shell[0])
        polygon = shapely.geometry.Polygon(shell)
        if not polygon.is_valid:
            # Attempt to fix invalid polygon or raise
            polygon = polygon.buffer(0)
            if not polygon.is_valid:
                raise ValueError("The provided polygon coordinates do not form a topologically valid polygon.")
        
        coords_json = json.dumps([[pt[0], pt[1]] for pt in shell])
        return WKTElement(polygon.wkt, srid=4326), coords_json

    def find_containing_zones(self, longitude: float, latitude: float) -> List[GeoZone]:
        """Finds all active GeoZones that cover the given point (longitude, latitude)."""
        active_zones = self.zone_repo.list_active()
        if not active_zones:
            return []

        point = shapely.geometry.Point(longitude, latitude)

        # If PostgreSQL + PostGIS is the underlying engine and PostGIS is enabled:
        if not is_sqlite:
            try:
                geom_pt = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
                stmt = select(GeoZone).where(
                    GeoZone.is_active == True,
                    func.ST_Covers(GeoZone.geom, geom_pt)
                )
                postgis_results = list(self.db.execute(stmt).scalars().all())
                return postgis_results
            except Exception as e:
                logger.warning(f"PostGIS ST_Covers query failed, falling back to spatial engine: {e}")

        # Standard / fallback spatial evaluation via Shapely
        containing = []
        for zone in active_zones:
            try:
                coords = json.loads(zone.coordinates_json)
                poly = shapely.geometry.Polygon(coords)
                # covers includes boundary points and interior
                if poly.covers(point):
                    containing.append(zone)
            except Exception as ex:
                logger.error(f"Error evaluating polygon for zone {zone.id}: {ex}")
        return containing

    def evaluate_zone_transitions(
        self,
        tourist_id: uuid.UUID,
        trip_id: uuid.UUID,
        latitude: float,
        longitude: float,
        recorded_at: datetime,
        location_event_id: Optional[uuid.UUID] = None,
    ) -> List[ZoneEvent]:
        """
        Calculates GeoZone ENTER and EXIT state transitions.
        
        Guarantees:
        - Exactly 1 ENTER event when outside -> inside
        - 0 events when remaining inside (inside -> inside)
        - Exactly 1 EXIT event when inside -> outside
        - 0 events when remaining outside (outside -> outside)
        """
        containing_zones = self.find_containing_zones(longitude=longitude, latitude=latitude)
        current_zone_map = {z.id: z for z in containing_zones}
        current_zone_ids = set(current_zone_map.keys())

        # Retrieve existing occupancy state
        existing_states = self.zone_repo.get_tourist_current_zones(tourist_id)
        previous_zone_ids = set(s.zone_id for s in existing_states)

        generated_events: List[ZoneEvent] = []

        # 1. ENTER transitions (zones now inside, but not previously)
        entered_zone_ids = current_zone_ids - previous_zone_ids
        for z_id in entered_zone_ids:
            event = ZoneEvent(
                tourist_id=tourist_id,
                trip_id=trip_id,
                zone_id=z_id,
                event_type=ZoneEventType.ENTER,
                location_event_id=location_event_id,
                occurred_at=recorded_at,
            )
            self.zone_repo.create_zone_event(event)
            self.zone_repo.set_tourist_in_zone(tourist_id, z_id, recorded_at)
            generated_events.append(event)
            logger.info(f"Tourist {tourist_id} ENTERED GeoZone '{current_zone_map[z_id].name}' ({current_zone_map[z_id].zone_type})")

        # 2. EXIT transitions (zones previously inside, but not now)
        exited_zone_ids = previous_zone_ids - current_zone_ids
        for z_id in exited_zone_ids:
            event = ZoneEvent(
                tourist_id=tourist_id,
                trip_id=trip_id,
                zone_id=z_id,
                event_type=ZoneEventType.EXIT,
                location_event_id=location_event_id,
                occurred_at=recorded_at,
            )
            self.zone_repo.create_zone_event(event)
            self.zone_repo.remove_tourist_from_zone(tourist_id, z_id)
            generated_events.append(event)
            logger.info(f"Tourist {tourist_id} EXITED GeoZone {z_id}")

        # 3. Inside -> Inside (unchanged): update last_seen_at
        retained_zone_ids = current_zone_ids & previous_zone_ids
        for z_id in retained_zone_ids:
            self.zone_repo.set_tourist_in_zone(tourist_id, z_id, recorded_at)

        return generated_events
