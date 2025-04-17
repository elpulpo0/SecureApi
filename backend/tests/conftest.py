import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from modules.database.session import Base
from modules.database.dependencies import get_users_db
from modules.api.main import app
from tests.setup_db import init_test_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # la clé magique
)
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(scope="function")
def db():
    init_test_db(engine)  # 👈 crée toutes les tables avant chaque test
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client_with_override(db):
    from modules.api.users.models import User, RefreshToken, Role
    from modules.database.session import Base

    _ = [User, RefreshToken, Role]

    Base.metadata.create_all(bind=db.get_bind())

    def override_get_db():
        yield db

    app.dependency_overrides[get_users_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
