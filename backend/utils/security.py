import hashlib
import bcrypt


# Fonction pour anonymiser un nom ou un prénom via hachage SHA256
def anonymize(name: str) -> str:
    """Hache un nom ou un prénom avec SHA256 pour anonymiser l'information."""
    return hashlib.sha256(name.encode("utf-8")).hexdigest()


# Fonction pour hacher un mot de passe avec bcrypt
def hash_password(password: str) -> str:
    """Hache un mot de passe avec bcrypt."""
    # Générer un salt unique pour chaque mot de passe
    salt = bcrypt.gensalt()

    # Hacher le mot de passe avec le salt
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)

    # Retourner le mot de passe haché
    return hashed_password.decode("utf-8")


# Fonction pour vérifier un mot de passe en utilisant bcrypt
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si le mot de passe en clair correspond au mot de passe haché avec bcrypt."""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def test_create_first_users_creates_admin_if_not_exists(monkeypatch, db):
    from modules.api.users.create_db import create_first_users

    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "adminpass")

    create_first_users()

    from modules.api.users.functions import anonymize, get_user_by_email

    email_hashed = anonymize("admin@example.com")

    user = get_user_by_email(email_hashed, db)
    assert user is not None
    assert user.role == "admin"
