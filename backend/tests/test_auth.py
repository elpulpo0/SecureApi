import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import timedelta
from jose import jwt
from modules.api.users.create_db import Base, User
from modules.api.auth.security import hash_password, anonymize
from modules.api.users.functions import get_user_by_email
from modules.api.auth.functions import create_access_token, authenticate_user
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
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


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


def test_refresh_token_generation():
    # Générer un refresh token avec type "refresh"
    email = "refresh@example.com"
    data = {"sub": email, "type": "refresh"}
    refresh_token = create_access_token(data, expires_delta=timedelta(days=7))

    # Décoder et valider manuellement (ce que ferait la route /refresh)
    decoded = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == email
    assert decoded["type"] == "refresh"

    # Simuler la génération d'un nouveau token
    new_access_token = create_access_token(
        data={"sub": decoded["sub"]}, expires_delta=timedelta(minutes=15)
    )
    new_decoded = jwt.decode(new_access_token, SECRET_KEY, algorithms=[ALGORITHM])
    assert new_decoded["sub"] == email
    assert "exp" in new_decoded


def test_refresh_route_works():
    # Générer un refresh token valide
    email = "testrefresh@example.com"
    refresh_token = create_access_token(
        data={"sub": email, "type": "refresh"},
        expires_delta=timedelta(days=7),
    )

    # Appeler la route /refresh avec le token
    response = client.post(
        "/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["token_type"] == "bearer"
