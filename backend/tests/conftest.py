import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modules.database.session import Base
from modules.database.dependencies import get_users_db
from fastapi.testclient import TestClient
from modules.api.main import app
from modules.api.users.models import RefreshToken, Role
_ = [RefreshToken, Role]  # 👈 Empêche optimisation



SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

# -- PARTAGE BASE --
@pytest.fixture(scope="session")
def db_engine():
    _ = RefreshToken
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="function")
def db(db_engine):
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client_with_override(db):
    def override_get_db():
        yield db
    app.dependency_overrides[get_users_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()