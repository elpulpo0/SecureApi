from modules.api.auth.security import verify_password, anonymize, hash_token
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import os
from dotenv import load_dotenv
from utils.logger_config import configure_logger
from modules.api.users.functions import get_user_by_email
from sqlalchemy.orm import Session
from modules.api.users.models import RefreshToken
from modules.api.users.schemas import TokenData
from fastapi.security import SecurityScopes, OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from modules.database.dependencies import get_users_db
from pydantic import ValidationError

# Configuration du logger
logger = configure_logger()

# Charger les variables d'environnement
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# Gestion de l'authentification avec OAuth2
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    scopes={
        "me": "Voir ses informations personnelles",
        "admin": "Accès aux opérations administratives",
        "reader": "Accès en lecture aux ressources",
    },
)


def create_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=60)
    )

    role = data.get("role")
    scopes_map = {"admin": ["admin"], "reader": ["reader"]}
    scopes = scopes_map.get(role, [])

    # Déterminer le type du token
    token_type = data.get("type", "access")
    to_encode["token_type"] = token_type

    if token_type == "access":
        to_encode["scopes"] = scopes

    to_encode["exp"] = expire

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Token {token_type} créé (scopes: {scopes}) – Expire à : {expire}")
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


def store_refresh_token(db: Session, user_id: int, token: str, expires_at: datetime):
    refresh_token = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(refresh_token)
    db.commit()


def find_refresh_token(db: Session, provided_token: str) -> RefreshToken | None:
    refresh_token = (
        db.query(RefreshToken).filter(RefreshToken.token == provided_token).first()
    )
    if refresh_token:
        logger.info(
            f"Refresh token found: {refresh_token.token}, expires_at: {refresh_token.expires_at}"
        )
    else:
        logger.warning("No refresh token found.")
    return refresh_token


def verify_token(provided_token: str, stored_hash: str) -> bool:
    return hash_token(provided_token) == stored_hash


def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_users_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        # Décodage du token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenData(**payload)  # Validation Pydantic
        email = token_data.sub
        token_scopes = token_data.scopes

    except JWTError:
        raise credentials_exception
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token payload validation error: {e.errors()}",
        )

    # Vérification des permissions
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

    # Recherche de l'utilisateur par email
    user = get_user_by_email(email, db)
    if not user:
        raise credentials_exception

    return token_data
