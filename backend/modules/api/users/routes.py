from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from modules.api.users.create_db import User
from modules.api.users.schemas import UserResponse
from utils.logger_config import configure_logger
from modules.database.dependencies import get_users_db


# Configuration du logger
logger = configure_logger()

# Gestion de l'authentification avec OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

users_router = APIRouter()


@users_router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Récupérer un utilisateur par son ID",
    description="Retourne les informations d'un utilisateur "
    "spécifique en fonction de son ID.")
def get_user(user_id: int, db: Session = Depends(get_users_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        is_active=user.is_active,
        role=user.role.role
    )
