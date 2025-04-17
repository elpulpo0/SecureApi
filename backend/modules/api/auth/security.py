import hashlib
import bcrypt


# Fonction pour anonymiser un nom ou un prénom via hachage SHA256
def anonymize(name: str) -> str:
    """Hache un nom ou un prénom avec SHA256 pour anonymiser l'information."""
    return hashlib.sha256(name.encode("utf-8")).hexdigest()


# Fonction pour anonymiser le refresh token via hachage SHA256
def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


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
