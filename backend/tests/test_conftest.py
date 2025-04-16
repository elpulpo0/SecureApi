import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modules.api.main import app
from modules.database.dependencies import get_users_db
from modules.database.session import Base

# 👇 Forcer l'import des modèles pour que SQLAlchemy les connaisse
from modules.api.users.models import RefreshToken, User # Ne pas supprimer

# ✅ Configuration in-memory SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 🧪 Fixture base de données
@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# 🔧 Override de dépendance FastAPI pour injecter la DB de test
@pytest.fixture
def client_with_override(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_users_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
