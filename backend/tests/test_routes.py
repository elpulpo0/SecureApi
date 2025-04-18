import pytest
from fastapi.testclient import TestClient
from modules.api.main import create_app
from modules.database.dependencies import get_users_db
from modules.api.auth.security import hash_password, anonymize
from modules.api.users.models import User, Role
import uuid
from utils.logger_config import configure_logger
from tests.test_auth import create_test_user

# Logger
logger = configure_logger()


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

    user.email_plain = unique_email
    return user


@pytest.fixture
def test_admin(db_session):

    unique_email = f"test_{uuid.uuid4()}@example.com"
    name = "admin"
    password = "testpass123"
    hashed_password = hash_password(password)

    admin = User(
        email=anonymize(unique_email),
        name=name,
        password=hashed_password,
        role_id="admin",
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    admin.email_plain = unique_email
    return admin


#############


def create_roles_if_not_exists(db_session):
    """Crée les rôles s'ils n'existent pas encore."""
    default_roles = ["admin", "reader"]
    for role_name in default_roles:
        role = db_session.query(Role).filter_by(role=role_name).first()
        if not role:
            db_session.add(Role(role=role_name))
    db_session.commit()


#####################


def test_roles_creation(client, db_session):
    """Test pour vérifier que les rôles sont créés"""
    # Créer les rôles s'ils n'existent pas
    create_roles_if_not_exists(db_session)

    # Vérifier que les rôles existent dans la base de données
    roles = db_session.query(Role).all()
    assert len(roles) == 2, "Les rôles par défaut ne sont pas présents"
    assert any(
        role.role == "admin" for role in roles
    ), "Le rôle 'admin' n'a pas été créé"
    assert any(
        role.role == "reader" for role in roles
    ), "Le rôle 'reader' n'a pas été créé"


def test_login_success(client, db_session):
    """Test de connexion avec succès"""

    # Créer les rôles s'ils n'existent pas
    create_roles_if_not_exists(db_session)

    # Création de l'utilisateur de test
    unique_email = f"test_{uuid.uuid4()}@example.com"
    user = create_test_user(db_session, unique_email)
    logger.debug(f"Created user: {unique_email, user.name}")

    # Connexion avec l'email et le mot de passe
    response = client.post(
        "/auth/login", data={"username": unique_email, "password": "testpass123"}
    )

    # Vérification du code de statut et des tokens dans la réponse
    assert response.status_code == 200
    json_data = response.json()

    # Vérification des tokens
    assert "access_token" in json_data
    assert "refresh_token" in json_data
    assert json_data["token_type"] == "bearer"


def test_login_failure_wrong_password(client, db_session):
    """Test de connexion avec un mot de passe incorrect"""

    # Créer un utilisateur avec un mot de passe connu
    email = f"test_{uuid.uuid4()}@example.com"
    create_test_user(db_session, email)

    # Effectuer la requête de connexion avec un mot de passe incorrect
    response = client.post(
        "/auth/login", data={"username": email, "password": "wrongpassword"}
    )

    # Vérification du code de réponse et du message d'erreur
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_failure_nonexistent_user(client):
    """Test de connexion avec un utilisateur inexistant"""
    response = client.post(
        "/auth/login", data={"username": "nouser@example.com", "password": "irrelevant"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_refresh_token_invalid(client):
    """Test de refresh token invalide"""
    response = client.post(
        "/auth/refresh", headers={"Authorization": "Bearer faketoken"}
    )
    assert response.status_code == 401
