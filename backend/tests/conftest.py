import pytest
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

# In-memory SQLite engine isolated for each test run
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
