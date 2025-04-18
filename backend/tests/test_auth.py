import os
import pytest
from datetime import timedelta, timezone, datetime
from jose import jwt
from sqlalchemy import inspect
from fastapi.testclient import TestClient
from modules.api.main import create_app
from modules.database.dependencies import get_users_db
from modules.api.users.models import User, Role
from modules.api.auth.security import hash_password, anonymize, hash_token
from modules.api.users.functions import get_user_by_email
from modules.api.auth.functions import (
    create_access_token,
    authenticate_user,
    store_refresh_token,
    find_refresh_token,
)
from utils.logger_config import configure_logger
from dotenv import load_dotenv

# Logger
logger = configure_logger()

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"


# Fixture pour l'application et la base de données de test
@pytest.fixture
def client(db_session):
    # Création de l'application FastAPI avec une DB de test
    app = create_app()
    app.dependency_overrides[get_users_db] = lambda: db_session

    # Création d’un client de test
    client = TestClient(app)
    yield client


@pytest.fixture
def test_user(db_session):
    import uuid

    unique_email = f"test_{uuid.uuid4()}@example.com"
    name = "test"
    password = "testpass123"
    hashed_password = hash_password(password)

    user = User(
        email=anonymize(unique_email),
        name=name,
        password=hashed_password,
        role_id="reader",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    user.email_plain = unique_email  # 👈 ajoute le mail clair pour les tests
    return user


def test_sanity_check_tables(db_session):
    inspector = inspect(db_session.get_bind())
    tables = inspector.get_table_names()
    print("🧪 Tables détectées :", tables)
    assert "refresh_tokens" in tables


def test_get_user_by_email_found(db_session, test_user):
    user = get_user_by_email(test_user.email, db_session)
    assert user is not None
    assert user.email == test_user.email


def test_get_user_by_email_not_found(db_session):
    user = get_user_by_email("doesnotexist@example.com", db_session)
    assert user is None


def test_authenticate_user_success(db_session, test_user):
    user = authenticate_user(db_session, test_user.email_plain, "testpass123")
    assert user is not False


def test_authenticate_user_wrong_password(db_session, test_user):
    user = authenticate_user(db_session, test_user.email, "wrongpassword")
    assert user is False


def test_authenticate_user_not_found(db_session):
    user = authenticate_user(db_session, "nouser@example.com", "any")
    assert user is False


def test_create_access_token():
    data = {"sub": "user_id"}
    token = create_access_token(data, expires_delta=timedelta(minutes=30))
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "user_id"
    assert "exp" in decoded


def create_test_user(db_session, email: str):
    # Assurez-vous que le rôle existe avant de l'assigner
    role = db_session.query(Role).filter(Role.role == "reader").first()
    if not role:
        role = Role(role="reader")  # Créez le rôle si nécessaire
        db_session.add(role)
        db_session.commit()
        db_session.refresh(role)

    user = User(
        email=anonymize(email),
        name="test",
        password=hash_password("testpass123"),
        role_id=role.id,  # Assigner le rôle à l'utilisateur
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_refresh_token_hashing(db_session):
    email = "testhashing@example.com"
    user = create_test_user(db_session, email)
    original_refresh_token = create_access_token(
        data={"sub": email, "role": "reader", "type": "refresh"},
        expires_delta=timedelta(days=7),
    )
    hashed_token = hash_token(original_refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    store_refresh_token(db_session, user.id, hashed_token, expires_at)

    refresh_token_db = find_refresh_token(db_session, hashed_token)
    assert refresh_token_db is not None
    assert refresh_token_db.token == hashed_token


def test_refresh_route_works(db_session, client):
    import uuid

    email = f"testrefresh_{uuid.uuid4()}@example.com"
    user = create_test_user(db_session, email)

    refresh_token = create_access_token(
        data={"sub": email, "role": "reader", "type": "refresh"},
        expires_delta=timedelta(days=7),
    )
    hashed_token = hash_token(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    store_refresh_token(db_session, user.id, hashed_token, expires_at)
    db_session.commit()

    print("✅ Refresh token stocké pour :", user.id)

    response = client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_token_validity(db_session, test_user):
    refresh_token = create_access_token(
        data={"sub": test_user.email, "role": "reader", "type": "refresh"},
        expires_delta=timedelta(days=7),
    )
    hashed_token = hash_token(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    store_refresh_token(db_session, test_user.id, hashed_token, expires_at)

    refresh_token_db = find_refresh_token(db_session, hashed_token)
    assert refresh_token_db is not None
    assert refresh_token_db.token == hashed_token
    assert refresh_token_db.expires_at.replace(tzinfo=timezone.utc) > datetime.now(
        timezone.utc
    )
