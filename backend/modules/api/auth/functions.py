from backend.modules.api.auth.security import verify_password, anonymize
from datetime import datetime, timedelta, timezone
from jose import jwt
import os
from dotenv import load_dotenv
from utils.logger_config import configure_logger
from modules.api.users.functions import get_user_by_email
from sqlalchemy.orm import Session

# Configuration du logger
logger = configure_logger()

# Charger les variables d'environnement
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=60)
    )
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Token d'accès créé avec expiration à : {expire}")

    return encoded_jwt


def authenticate_user(db: Session, email: str, password: str):
    """Authentifie un utilisateur en vérifiant son email et son mot de passe."""
    logger.info("Authentification de l'utilisateur...")

    # Hacher l'email fourni par l'utilisateur pour la comparaison
    anonymized_email = anonymize(email)  # Hacher l'email

    # Récupérer l'utilisateur en utilisant l'email haché
    user = get_user_by_email(anonymized_email, db)

    # Vérifier si l'utilisateur existe et si le mot de passe est valide
    if not user:
        logger.info("Utilisateur non trouvé.")
        return False

    if not verify_password(password, user.password):
        logger.info("Mot de passe invalide.")
        return False

    logger.info("Utilisateur authentifié avec succès")
    return user
