# ADR-004: PostGIS Spatial Storage and Geofencing Strategy

## Status
ACCEPTED

## Context
KIROSHI requires high-performance spatial queries for point ingestion, trajectory history retrieval, polygon containment, and hazard geofencing. Storing coordinates simply as raw numeric `latitude` and `longitude` columns requires in-memory calculation in application code, preventing indexed database-level containment queries and spatial joins.

## Decision
We adopted **PostgreSQL 16 with PostGIS 3.4** as the primary spatial database engine, utilizing **GeoAlchemy2** for ORM mapping and **Shapely** for client-side geometric validation and local testing fallback.

Key design choices:
1. **SRID 4326 (WGS 84)**: Standardized all spatial geometries on EPSG:4326 decimal degrees.
2. **PostGIS Point & Polygon Geometries**:
   - `LocationEvent.location_point`: `Geometry(geometry_type='POINT', srid=4326)`.
   - `GeoZone.geometry`: `Geometry(geometry_type='POLYGON', srid=4326)`.
3. **Spatial GIST Indexes**: Created GIST indexes (`idx_location_events_point`, `idx_geo_zones_geometry`) enabling $O(\log N)$ bounding-box and containment checks.
4. **`ST_Covers` Operator**: Used `ST_Covers(geometry, ST_SetSRID(ST_MakePoint(lon, lat), 4326))` to accurately detect points on polygon boundaries in addition to points strictly inside.
5. **Stateful Transition Machine**: Maintained a dedicated `TouristZoneState` table to track whether a tourist is currently inside or outside each active zone. State transitions (`ENTER` and `EXIT`) are edge-triggered and logged to an immutable `ZoneEvent` audit table, guaranteeing zero duplicate alerts.
6. **Dual-Engine Test Strategy**: To allow rapid local unit and integration testing without requiring local PostgreSQL installation on every developer machine, we implemented SQLite user-defined functions with Shapely bindings (`ST_Covers`, `ST_SetSRID`, `AsEWKB`) that mirror PostGIS semantics in-memory, while full PostGIS tests run against `postgis/postgis:16-3.4` in CI.

## Consequences
- **Positive**: Native spatial query performance, robust polygon indexing, and exact geofence boundary handling. Zero alert oscillation for stationary tourists inside zones.
- **Negative**: Adds `geoalchemy2`, `shapely`, and `psycopg2-binary` dependencies to the backend environment. Requires PostGIS extension enabled in target PostgreSQL instances.
