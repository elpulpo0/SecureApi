from datetime import datetime, timedelta, timezone
from modules.api.users.create_db import User
from utils.security import verify_password, anonymize
from sqlalchemy.orm import Session
from jose import jwt
import os
from dotenv import load_dotenv
from utils.logger_config import configure_logger

# Configuration du logger
logger = configure_logger()

# Charger les variables d'environnement
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
ALGORITHM = "HS256"  # Algorithme de codage pour JWT


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Token d'accès créé avec expiration à : {expire}")

    return encoded_jwt


def get_user_by_email(email: str, db: Session):
    # Effectuer la recherche dans la base de données avec l'email anonymisé
    user = db.query(User).filter(User.email == email).first()

    return user


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
