from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.core.config import settings

is_sqlite = settings.DATABASE_URL.startswith("sqlite")

connect_args = {}
if is_sqlite:
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True,
)

# Enforce foreign key constraints in SQLite and configure GeoAlchemy2 fallback
if is_sqlite:
    def as_ewkb(val):
        if val is None:
            return None
        if isinstance(val, str):
            if ";" in val:
                val = val.split(";", 1)[1]
            try:
                import shapely.wkt
                import shapely.wkb
                geom = shapely.wkt.loads(val)
                return shapely.wkb.dumps(geom, hex=True, srid=4326)
            except Exception:
                return val
        return val

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

        # Register Spatial UDF fallbacks for environments without SpatiaLite
        dbapi_connection.create_function("GeomFromEWKT", 1, lambda x: x)
        dbapi_connection.create_function("GeomFromText", 1, lambda x: x)
        dbapi_connection.create_function("ST_GeomFromText", 1, lambda x: x)
        dbapi_connection.create_function("AsEWKB", 1, as_ewkb)
        dbapi_connection.create_function("ST_AsEWKB", 1, as_ewkb)
        dbapi_connection.create_function("AsBinary", 1, as_ewkb)
        dbapi_connection.create_function("ST_AsBinary", 1, as_ewkb)

    try:
        from geoalchemy2 import Geometry
        from sqlalchemy.ext.compiler import compiles
        import geoalchemy2.admin.dialects.sqlite as geo_sqlite

        geo_sqlite.after_create = lambda *args, **kwargs: None
        geo_sqlite.before_create = lambda *args, **kwargs: None
        geo_sqlite.after_drop = lambda *args, **kwargs: None
        geo_sqlite.before_drop = lambda *args, **kwargs: None
        geo_sqlite.reflect_geometry_column = lambda *args, **kwargs: None

        @compiles(Geometry, "sqlite")
        def compile_geometry_sqlite(type_, compiler, **kw):
            return "GEOMETRY"
    except ImportError:
        pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
