import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import timedelta
from jose import jwt
import os

from modules.api.users.create_db import Base, User
from utils.security import hash_password, anonymize
from modules.api.users.functions import (
    create_access_token,
    authenticate_user,
    get_user_by_email,
)

# Setup variables d'env
SECRET_KEY = os.getenv("SECRET_KEY", "test-secret-key")
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
    password = "testpass123"
    hashed_password = hash_password(password)

    user = User(
        email=anonymize(email), password=hashed_password, role="user", is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


### 🔹 TESTS


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
