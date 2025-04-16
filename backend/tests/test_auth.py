import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import timedelta, timezone, datetime
from jose import jwt
from modules.api.users.create_db import Base, User
from modules.api.auth.security import hash_password, anonymize, hash_token
from modules.api.users.functions import get_user_by_email
from modules.api.auth.functions import (
    create_access_token,
    authenticate_user,
    store_refresh_token,
    find_refresh_token,
)
from fastapi.testclient import TestClient
from modules.api.main import app

client = TestClient(app)

# Setup variables d'env
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# Configuration DB de test (SQLite in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Fixture de base de données
@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


# Fixture utilisateur
@pytest.fixture
def test_user(db):
    email = "test@example.com"
    name = "test"
    password = "testpass123"
    hashed_password = hash_password(password)

    user = User(
        email=anonymize(email),
        name=name,
        password=hashed_password,
        role_id="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# 🔹 TESTS


def test_get_user_by_email_found(db, test_user):
    user = get_user_by_email(test_user.email, db)
    assert user is not None
    assert user.email == test_user.email


def test_get_user_by_email_not_found(db):
    user = get_user_by_email("doesnotexist@example.com", db)
    assert user is None


def test_authenticate_user_success(db, test_user):
    user = authenticate_user(db, "test@example.com", "testpass123")
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

    # Générer un refresh token initial
    original_refresh_token = create_access_token(
        data={"sub": email, "role": "user", "type": "refresh"},
        expires_delta=timedelta(days=7),
    )
    hashed_token = hash_token(
        original_refresh_token
    )  # Hacher le token avant de le stocker
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    # Enregistrer le token haché
    store_refresh_token(db, user.id, hashed_token, expires_at)

    # Vérifier que le token est bien stocké haché
    refresh_token_db = find_refresh_token(
        db, hashed_token
    )  # Passer directement le token haché ici
    assert refresh_token_db is not None
    assert (
        refresh_token_db.token == hashed_token
    )  # Le token dans la DB doit correspondre exactement au token haché


def test_refresh_route_works(db):
    email = "testrefresh@example.com"
    user = create_test_user(db, email)

    # Générer un refresh token initial
    old_refresh_token = create_access_token(
        data={"sub": email, "role": "user", "type": "refresh"},
        expires_delta=timedelta(days=7),
    )
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    store_refresh_token(db, user.id, old_refresh_token, expires_at)

    # Appel avec le vieux token
    response = client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {old_refresh_token}"},
    )
    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert (
        "refresh_token" in json_data
    )  # On vérifie que le refresh token est bien retourné
    assert json_data["token_type"] == "bearer"

    new_refresh_token = json_data["refresh_token"]

    # Réessai avec l'ancien token (devrait échouer car invalidé)
    response_reuse = client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {old_refresh_token}"},
    )
    assert response_reuse.status_code == 401

    # Réessai avec le nouveau (doit fonctionner)
    response_valid = client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {new_refresh_token}"},
    )
    assert response_valid.status_code == 200


def test_refresh_token_validity(db, test_user):
    # Générer un refresh token
    refresh_token = create_access_token(
        data={"sub": test_user.email, "role": "user", "type": "refresh"},
        expires_delta=timedelta(days=7),
    )
    hashed_token = hash_token(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    store_refresh_token(db, test_user.id, hashed_token, expires_at)

    # Récupérer le token depuis la base de données
    refresh_token_db = find_refresh_token(db, hashed_token)
    assert refresh_token_db is not None
    assert refresh_token_db.token == hashed_token
    assert refresh_token_db.expires_at > datetime.now(timezone.utc).astimezone(timezone.utc)
