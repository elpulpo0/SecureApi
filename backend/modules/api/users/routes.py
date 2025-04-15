from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from jose import JWTError, jwt
import os
from dotenv import load_dotenv
from utils.security import anonymize, hash_password
from modules.api.users.create_db import User
from modules.api.users.schemas import UserResponse, Token, UserCreate, RoleUpdate
from modules.api.users.functions import (
    get_user_by_email,
    create_access_token,
    authenticate_user,
)
from utils.logger_config import configure_logger
from modules.database.dependencies import get_users_db
from modules.api.users.models import Role

load_dotenv()  # Charge les variables d'environnement depuis .env

# Configuration du logger
logger = configure_logger()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180

# Gestion de l'authentification avec OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

users_router = APIRouter()


@users_router.post(
    "/login",
    response_model=Token,
    summary="Connexion et génération d'un token JWT",
    description="Vérifie les informations de connexion et retourne "
    "un token d'authentification JWT si les identifiants sont corrects.",
    tags=["Utilisateurs"],
)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_users_db),
):
    # Authentifier l'utilisateur
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@users_router.get(
    "/users/me",
    response_model=UserResponse,
    summary="Récupérer les informations de l'utilisateur connecté",
    description="Retourne les détails de l'utilisateur authentifié en utilisant son token.",
    tags=["Utilisateurs"],
)
def read_users_me(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_users_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Décoder le token pour vérifier la validité et l'expiration
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": True},
        )
        anonymized_email: str = payload.get(
            "sub"
        )  # Utiliser l'email anonymisé dans le payload

        # Vérifier que le token contient un email
        if anonymized_email is None:
            logger.error("Token ne contient pas d'email.")
            raise credentials_exception

        # Récupérer l'utilisateur en utilisant l'email anonymisé
        user = get_user_by_email(anonymized_email, db)

        # Vérifier si l'utilisateur existe
        if user is None:
            logger.error("Utilisateur non trouvé.")
            raise credentials_exception

        return UserResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            role=user.role.role
        )

    except JWTError as e:
        # Log d'erreur si le token est invalide ou expiré
        logger.error(f"Erreur de JWT: {str(e)}")
        raise credentials_exception


@users_router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Récupérer un utilisateur par son ID",
    description="Retourne les informations d'un utilisateur "
    "spécifique en fonction de son ID.",
    tags=["Utilisateurs"],
)
def get_user(user_id: int, db: Session = Depends(get_users_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user


@users_router.get(
    "/users/",
    response_model=list[UserResponse],
    summary="Lister tous les utilisateurs",
    tags=["Utilisateurs"],
)
def get_all_users(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_users_db)
):
    """Seuls les administrateurs peuvent voir tous les utilisateurs."""

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        requesting_user = get_user_by_email(email, db)

        if not requesting_user:
            raise HTTPException(
                status_code=401, detail="Utilisateur non trouvé."
            )

        # ✅ Correction ici : comparaison avec le nom du rôle
        if requesting_user.role.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Accès refusé : réservé aux administrateurs.",
            )

        # ✅ Renvoi formaté pour Pydantic
        return [
            UserResponse(
                id=u.id,
                email=u.email,
                is_active=u.is_active,
                role=u.role.role
            )
            for u in db.query(User).all()
        ]

    except JWTError:
        raise HTTPException(
            status_code=401, detail="Token invalide ou expiré."
        )


@users_router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un utilisateur",
    description="Supprime un utilisateur spécifique en fonction de son ID.",
    tags=["Utilisateurs"],
)
def delete_user(
    user_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_users_db),
):
    """Seuls les administrateurs peuvent supprimer un utilisateur."""

    try:
        # Décodage du token JWT pour obtenir l'email de l'utilisateur qui fait la requête
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        requesting_user = get_user_by_email(email, db)

        if not requesting_user:
            raise HTTPException(
                status_code=401, detail="Utilisateur non trouvé."
            )

        # Vérifier que l'utilisateur est un admin
        if requesting_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Accès refusé : réservé aux administrateurs.",
            )

        # Suppression de l'utilisateur
        user_to_delete = db.query(User).filter(User.id == user_id).first()
        if not user_to_delete:
            raise HTTPException(
                status_code=404, detail="Utilisateur non trouvé."
            )

        db.delete(user_to_delete)
        db.commit()

        return {"message": "Utilisateur supprimé"}

    except JWTError:
        raise HTTPException(
            status_code=401, detail="Token invalide ou expiré."
        )


@users_router.post(
    "/users/",
    response_model=UserResponse,
    summary="Créer un nouvel utilisateur",
    description="Ajoute un nouvel utilisateur à la base de données.",
    tags=["Utilisateurs"],
    status_code=status.HTTP_201_CREATED,
)
def create_user(user_data: UserCreate, db: Session = Depends(get_users_db)):
    """Créer un nouvel utilisateur avec email, mot de passe et rôle."""

    # Vérifier si l'utilisateur existe déjà
    anonymized_email = anonymize(user_data.email)
    existing_user = get_user_by_email(anonymized_email, db)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Un utilisateur avec cet email existe déjà",
        )

    # Récupérer le rôle par défaut
    role_obj = db.query(Role).filter_by(role="reader").first()
    if not role_obj:
        raise HTTPException(status_code=500, detail="Le rôle 'reader' est introuvable")

    # Créer un nouvel utilisateur
    new_user = User(
        email=anonymized_email,
        password=hash_password(user_data.password),
        role_id=role_obj.id,
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        is_active=new_user.is_active,
        role=new_user.role.role
    )


@users_router.patch(
    "/users/{user_id}/role",
    summary="Modifier le rôle d'un utilisateur",
    description="Permet à un administrateur de modifier le rôle d'un utilisateur.",
    tags=["Utilisateurs"],
)
def update_user_role(
    user_id: int,
    role_update: RoleUpdate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_users_db),
):
    try:
        # Authentifier l'utilisateur qui fait la demande
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        requesting_user = get_user_by_email(email, db)

        if not requesting_user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé.")

        if requesting_user.role != "admin":
            raise HTTPException(
                status_code=403, detail="Accès refusé : réservé aux administrateurs."
            )

        # Récupérer l'utilisateur cible
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=404, detail="Utilisateur à modifier non trouvé."
            )

        # Mettre à jour le rôle
        user.role = role_update.role
        db.commit()
        db.refresh(user)

        return {"message": f"Rôle de l'utilisateur mis à jour en '{user.role}'."}

    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré.")
