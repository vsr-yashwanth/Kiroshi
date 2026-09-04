import os
import sys
import pytest

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.domain.models.user import User
from backend.app.domain.models.tourist_profile import TouristProfile
from backend.app.domain.models.enums import UserRole

# Ensure GeoAlchemy2 SQLite fallback is applied for tests
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

import shapely.wkt
import shapely.wkb
from sqlalchemy import event
import backend.app.core.database as core_db

# In-memory SQLite engine isolated for each test run
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
core_db.engine = engine


def as_ewkb(*args):
    if not args or args[0] is None:
        return None
    val = args[0]
    if isinstance(val, str):
        if ";" in val:
            val = val.split(";", 1)[1]
        try:
            geom = shapely.wkt.loads(val)
            return shapely.wkb.dumps(geom, hex=True, srid=4326)
        except Exception:
            return val
    return val


@event.listens_for(engine, "connect")
def register_test_sqlite_udfs(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
    dbapi_connection.create_function("GeomFromEWKT", -1, lambda *args: args[0] if args else None)
    dbapi_connection.create_function("GeomFromText", -1, lambda *args: args[0] if args else None)
    dbapi_connection.create_function("ST_GeomFromText", -1, lambda *args: args[0] if args else None)
    dbapi_connection.create_function("AsEWKB", -1, as_ewkb)
    dbapi_connection.create_function("ST_AsEWKB", -1, as_ewkb)
    dbapi_connection.create_function("AsBinary", -1, as_ewkb)
    dbapi_connection.create_function("ST_AsBinary", -1, as_ewkb)
    dbapi_connection.create_function("RecoverGeometryColumn", -1, lambda *args: 1)
    dbapi_connection.create_function("DiscardGeometryColumn", -1, lambda *args: 1)
    dbapi_connection.create_function("CheckSpatialIndex", -1, lambda *args: None)
    dbapi_connection.create_function("InitSpatialMetaData", -1, lambda *args: 1)
    dbapi_connection.create_function("CreateSpatialIndex", -1, lambda *args: 1)
    dbapi_connection.create_function("DisableSpatialIndex", -1, lambda *args: 1)


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
core_db.SessionLocal = TestingSessionLocal


@pytest.fixture(scope="function")
def db_session() -> Generator:
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def tourist_user(db_session) -> User:
    user = User(
        email="tourist1@example.com",
        hashed_password=get_password_hash("Password123!"),
        full_name="Alice Traveler",
        role=UserRole.TOURIST,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    profile = TouristProfile(
        user_id=user.id,
        nationality="Canadian",
        emergency_contact_name="Bob Traveler",
        emergency_contact_phone="+15551234567",
        consent_given=True,
    )
    db_session.add(profile)
    db_session.commit()
    return user


@pytest.fixture
def tourist_user_2(db_session) -> User:
    user = User(
        email="tourist2@example.com",
        hashed_password=get_password_hash("Password123!"),
        full_name="Charlie Roamer",
        role=UserRole.TOURIST,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    profile = TouristProfile(
        user_id=user.id,
        nationality="German",
        emergency_contact_name="Diana Roamer",
        emergency_contact_phone="+49123456789",
        consent_given=True,
    )
    db_session.add(profile)
    db_session.commit()
    return user


@pytest.fixture
def authority_user(db_session) -> User:
    user = User(
        email="authority@example.com",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="Chief Inspector Ray",
        role=UserRole.AUTHORITY,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def tourist_token_headers(tourist_user) -> dict:
    token = create_access_token(subject=tourist_user.id, role=tourist_user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def tourist_2_token_headers(tourist_user_2) -> dict:
    token = create_access_token(subject=tourist_user_2.id, role=tourist_user_2.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def authority_token_headers(authority_user) -> dict:
    token = create_access_token(subject=authority_user.id, role=authority_user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def responder_user(db_session) -> User:
    user = User(
        email="responder@example.com",
        hashed_password=get_password_hash("ResponderPass123!"),
        full_name="Officer Kenji",
        role=UserRole.RESPONDER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def responder_token_headers(responder_user) -> dict:
    token = create_access_token(subject=responder_user.id, role=responder_user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(db_session) -> User:
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="System Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token_headers(admin_user) -> dict:
    token = create_access_token(subject=admin_user.id, role=admin_user.role.value)
    return {"Authorization": f"Bearer {token}"}

