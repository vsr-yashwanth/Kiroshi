# Geospatial Geofencing & State Transitions — KIROSHI v0.2

> Status: IMPLEMENTED (v0.2) | Service: `GeospatialService`

---

## 1. Spatial Foundation

KIROSHI v0.2 implements real-time spatial geofencing using PostgreSQL 16 and PostGIS 3.4.

### 1.1 Coordinate System & SRID
All spatial primitives are standardized on **WGS 84 (EPSG:4326)**:
- Coordinates are expressed in decimal degrees: `(longitude, latitude)`.
- Notice the PostGIS order: `ST_MakePoint(longitude, latitude)`.
- SRID 4326 is explicitly declared on all geometry columns.

### 1.2 Spatial Containment Query
Containment is calculated using the PostGIS `ST_Covers` function indexed via GIST:

```sql
SELECT gz.id, gz.name, gz.zone_type, gz.coordinates_json
FROM geo_zones gz
WHERE gz.is_active = TRUE
  AND ST_Covers(
    gz.geometry,
    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
  );
```

> **Why `ST_Covers` instead of `ST_Contains`?**  
> `ST_Contains` does not consider a point on the boundary of a polygon to be inside. `ST_Covers` includes points strictly inside as well as points lying directly on polygon boundary lines.

---

## 2. Zone Types & Hazard Semantics

| Zone Type | Operational Meaning | Visual Display | Authority Action |
|---|---|---|---|
| `SAFE` | Verified tourist corridors, designated camping zones, authorized routes | Emerald green border | Normal monitoring |
| `RESTRICTED` | Permits required, fragile wildlife reserves, seasonal closures | Amber warning border | Monitored entry |
| `HIGH_RISK` | Avalanche paths, flood zones, landslide terrain, active hazards | Red warning border with danger pulse | Immediate alert & verification |
| `CUSTOM` | Ad-hoc administrative perimeters, temporary closures | Indigo border | Custom policy evaluation |

---

## 3. State Transition Engine & Truth Table

A common failure in real-time tracking systems is **event oscillation / spamming**, where successive GPS pings inside a zone generate dozens of redundant `ENTER` notifications.

KIROSHI resolves this by maintaining persistent occupancy state in `tourist_zone_states`:

```
                    ┌─────────────────────────┐
                    │     OUTSIDE A ZONE      │
                    └───────────┬─────────────┘
                                │
                                │ ST_Covers evaluates TRUE
                                ▼
                    ┌─────────────────────────┐
                    │      EMIT 'ENTER'       │
                    │  Update state: is_inside│
                    └───────────┬─────────────┘
                                │
         ST_Covers remains TRUE │
       (No duplicate events!)   │
                                ▼
                    ┌─────────────────────────┐
                    │      INSIDE A ZONE      │
                    └───────────┬─────────────┘
                                │
                                │ ST_Covers evaluates FALSE
                                ▼
                    ┌─────────────────────────┐
                    │       EMIT 'EXIT'       │
                    │  Update state: is_inside│
                    └───────────┬─────────────┘
                                │
        ST_Covers remains FALSE │
       (No duplicate events!)   │
                                ▼
                    ┌─────────────────────────┐
                    │     OUTSIDE A ZONE      │
                    └─────────────────────────┘
```

### Transition Table

| Previous State (`TouristZoneState.is_inside`) | Evaluated Containment (`ST_Covers`) | Action Taken | Event Generated |
|---|---|---|---|
| `False` or None | `True` | Update state to `True`, set `entered_at = now()` | `ZoneEvent(event_type='ENTER')` |
| `True` | `True` | Retain state | *None* |
| `True` | `False` | Update state to `False`, set `exited_at = now()` | `ZoneEvent(event_type='EXIT')` |
| `False` or None | `False` | No change | *None* |

---

## 4. Polygon Geometry Validation

Before persisting a `GeoZone`:
1. **Coordinate Count**: Polygons must have at least 3 distinct vertices.
2. **Ring Closure**: The first and last coordinate pair in the boundary ring are automatically closed (`coords[0] == coords[-1]`).
3. **WKT Serialization**: The coordinates are formatted as `POLYGON((lon1 lat1, lon2 lat2, ...))` and loaded via `ST_GeomFromText` or Shapely `Polygon`.
4. **Self-Intersection Check**: Shapely verifies `polygon.is_valid` before database insertion.
