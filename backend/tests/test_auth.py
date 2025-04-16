import os
import pytest
from datetime import timedelta, timezone, datetime
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modules.database.session import Base
from modules.api.main import app
from modules.database.dependencies import get_users_db
from modules.api.users.models import RefreshToken, Role
from modules.api.users.create_db import User
from modules.api.auth.security import hash_password, anonymize, hash_token
from modules.api.users.functions import get_user_by_email
from modules.api.auth.functions import (
    create_access_token,
    authenticate_user,
    store_refresh_token,
    find_refresh_token,
)
from fastapi.testclient import TestClient
from utils.logger_config import configure_logger

# Logger
logger = configure_logger()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# In-memory SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)


# 📌 Fixture DB
@pytest.fixture(scope="function")
def db():
    _ = [RefreshToken, Role]
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

# 📌 Fixture client
@pytest.fixture
def client_with_override(db):
    def override_get_db():
        yield db
    app.dependency_overrides[get_users_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db):
    import uuid
    unique_email = f"test_{uuid.uuid4()}@example.com"  # 👈 génère un email unique
    name = "test"
    password = "testpass123"
    hashed_password = hash_password(password)

    user = User(
        email=anonymize(unique_email),
        name=name,
        password=hashed_password,
        role_id="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def db():
    from modules.api.users.models import RefreshToken, Role  # 👈 Ajoute Role aussi si nécessaire
    _ = [RefreshToken, Role]  # 👈 Force l'import pour que SQLAlchemy les connaisse
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_get_user_by_email_found(db, test_user):
    user = get_user_by_email(test_user.email, db)
    assert user is not None
    assert user.email == test_user.email


def test_get_user_by_email_not_found(db):
    user = get_user_by_email("doesnotexist@example.com", db)
    assert user is None


def test_authenticate_user_success(db, test_user):
    user = authenticate_user(db, test_user.email, "testpass123")
    assert user is not False


def test_authenticate_user_wrong_password(db, test_user):
    user = authenticate_user(db, test_user.email, "wrongpassword")
    assert user is False


def test_authenticate_user_not_found(db):
    user = authenticate_user(db, "nouser@example.com", "any")
    assert user is False


def test_create_access_token():
    data = {"sub": "user_id"}
    token = create_access_token(data, expires_delta=timedelta(minutes=30))
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "user_id"
    assert "exp" in decoded


def create_test_user(db, email: str):
    user = User(
        email=anonymize(email),
        name="test",
        password=hash_password("testpass123"),
        role_id="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_refresh_token_hashing(db):
    email = "testhashing@example.com"
    user = create_test_user(db, email)
    original_refresh_token = create_access_token(
        data={"sub": email, "role": "user", "type": "refresh"},
        expires_delta=timedelta(days=7),
    )
    hashed_token = hash_token(original_refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    store_refresh_token(db, user.id, hashed_token, expires_at)

    refresh_token_db = find_refresh_token(db, hashed_token)
    assert refresh_token_db is not None
    assert refresh_token_db.token == hashed_token


def test_refresh_route_works(db, client_with_override):
    email = "testrefresh@example.com"
    user = create_test_user(db, email)
    old_refresh_token = create_access_token(
        data={"sub": email, "type": "refresh"},
        expires_delta=timedelta(days=7),
    )
    hashed_old = hash_token(old_refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    store_refresh_token(db, user.id, hashed_old, expires_at)

    response = client_with_override.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {old_refresh_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

    new_refresh_token = data["refresh_token"]

    response_reuse = client_with_override.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {old_refresh_token}"},
    )
    assert response_reuse.status_code == 401

    response_valid = client_with_override.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {new_refresh_token}"},
    )
    assert response_valid.status_code == 200


def test_refresh_token_validity(db, test_user):
    refresh_token = create_access_token(
        data={"sub": test_user.email, "role": "user", "type": "refresh"},
        expires_delta=timedelta(days=7),
    )
    hashed_token = hash_token(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    store_refresh_token(db, test_user.id, hashed_token, expires_at)

    refresh_token_db = find_refresh_token(db, hashed_token)
    assert refresh_token_db is not None
    assert refresh_token_db.token == hashed_token
    assert refresh_token_db.expires_at.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc)