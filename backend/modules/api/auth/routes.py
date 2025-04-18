from utils.logger_config import configure_logger
from datetime import timedelta, timezone, datetime
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException, status
from modules.api.users.schemas import Token
from modules.database.dependencies import get_users_db
from sqlalchemy.orm import Session
from modules.api.auth.functions import (
    authenticate_user,
    create_token,
    store_refresh_token,
)
import os
from jose import JWTError, jwt
from modules.api.users.schemas import UserResponse, UserCreate, RoleUpdate
from modules.api.users.create_db import User, Role
from modules.api.users.functions import get_user_by_email
from modules.api.auth.functions import find_refresh_token, get_current_user, oauth2_scheme
from modules.api.auth.security import anonymize, hash_password, hash_token
from fastapi.responses import JSONResponse
from uuid import uuid4

load_dotenv()

# Configuration du logger
logger = configure_logger()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

auth_router = APIRouter()

@auth_router.post("/login", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_users_db),
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=15)
    refresh_token_expires = timedelta(days=7)

    access_token = create_token(
        data={"sub": user.email, "role": user.role.role, "type": "access"},
        expires_delta=access_token_expires,
    )

    refresh_token = create_token(
        data={"sub": user.email, "type": "refresh"},
        expires_delta=refresh_token_expires,
    )

    refresh_expiry = datetime.now(timezone.utc) + refresh_token_expires
    hashed_token = hash_token(refresh_token)
    store_refresh_token(db, user.id, hashed_token, refresh_expiry)

    return JSONResponse(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    )


@auth_router.post("/refresh", response_model=Token)
def refresh_token(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_users_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        role = payload.get("role")
        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(
                status_code=401, detail="Token invalide pour rafraîchissement"
            )
    except JWTError:
        raise HTTPException(status_code=401, detail="Token non valide")

    hashed_token = hash_token(token)
    refresh_token_db = find_refresh_token(db, hashed_token)

    if not refresh_token_db:
        raise HTTPException(
            status_code=401,
            detail="Refresh token introuvable")

    if refresh_token_db.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expiré")

    refresh_token_db.revoked = True

    hashed_email = anonymize(email)
    user = get_user_by_email(hashed_email, db)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    new_access_token = create_token(
        data={"sub": email, "role": role}, expires_delta=timedelta(minutes=15)
    )

    new_refresh_token = create_token(
        data={
            "sub": email, "role": role, "type": "refresh", "jti": str(uuid4())
        }, expires_delta=timedelta(days=7)
    )
    hashed_new_refresh_token = hash_token(new_refresh_token)
    refresh_expiry = datetime.now(timezone.utc) + timedelta(days=7)

    store_refresh_token(db, user_id=user.id, token=hashed_new_refresh_token, expires_at=refresh_expiry)

    db.commit()

    return JSONResponse(
        {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
    )


@auth_router.get("/users/me", response_model=UserResponse)
def read_users_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_users_db)
):
    user = get_user_by_email(current_user.sub, db)
    
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        is_active=user.is_active,
        role=user.role.role,
    )


@auth_router.get("/users/", response_model=list[UserResponse])
def get_all_users(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_users_db)
):
    # Vérification que l'utilisateur actuel a les permissions nécessaires pour voir la liste des utilisateurs
    if "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=403,
            detail="Accès refusé : réservé aux administrateurs.",
        )

    # Récupérer tous les utilisateurs de la base de données
    users = db.query(User).all()

    # Retourner les utilisateurs sous forme de liste de UserResponse
    return [
        UserResponse(
            id=u.id,
            name=u.name,
            email=u.email,
            is_active=u.is_active,
            role=u.role.role,
        )
        for u in users
    ]


@auth_router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_users_db),
):
    # Vérification que l'utilisateur actuel a les permissions nécessaires pour supprimer un utilisateur
    if "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=403,
            detail="Accès refusé : réservé aux administrateurs.",
        )

    # Recherche de l'utilisateur à supprimer dans la base de données
    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(
            status_code=404,
            detail="Utilisateur non trouvé."
        )

    # Suppression de l'utilisateur
    db.delete(user_to_delete)
    db.commit()

    return JSONResponse({"message": "Utilisateur supprimé"})


@auth_router.post("/users/", response_model=UserResponse)
def create_user(user_data: UserCreate, db: Session = Depends(get_users_db)):
    anonymized_email = anonymize(user_data.email)
    existing_user = get_user_by_email(anonymized_email, db)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Un utilisateur avec cet email existe déjà",
        )

    role_obj = db.query(Role).filter_by(role="reader").first()
    if not role_obj:
        raise HTTPException(status_code=500, detail="Le rôle 'reader' est introuvable")

    new_user = User(
        email=anonymized_email,
        name=user_data.name,
        password=hash_password(user_data.password),
        role_id=role_obj.id,
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        name=new_user.name,
        email=new_user.email,
        is_active=new_user.is_active,
        role=new_user.role.role,
    )


@auth_router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role_update: RoleUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_users_db),
):
    # Vérification que l'utilisateur actuel a les permissions nécessaires pour modifier un rôle
    if "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=403,
            detail="Accès refusé : réservé aux administrateurs."
        )

    # Recherche de l'utilisateur à modifier dans la base de données
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404, 
            detail="Utilisateur à modifier non trouvé."
        )

    # Recherche du nouveau rôle à assigner à l'utilisateur
    new_role = db.query(Role).filter(Role.role == role_update.role).first()
    if not new_role:
        raise HTTPException(
            status_code=404, 
            detail="Rôle non trouvé."
        )

    # Mise à jour du rôle de l'utilisateur
    user.role_id = new_role.id
    db.commit()
    db.refresh(user)

    return JSONResponse(
        {"message": f"Rôle de l'utilisateur mis à jour en '{new_role.role}'."}
    )