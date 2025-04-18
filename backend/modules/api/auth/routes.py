from utils.logger_config import configure_logger
from datetime import timedelta, timezone, datetime
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException, status
from modules.api.users.schemas import Token
from modules.database.dependencies import get_users_db
from sqlalchemy.orm import Session
from modules.api.auth.functions import (
    authenticate_user,
    create_access_token,
    store_refresh_token,
)
import os
from jose import JWTError, jwt
from modules.api.users.schemas import UserResponse, UserCreate, RoleUpdate
from modules.api.users.models import RefreshToken
from modules.api.users.create_db import User, Role
from modules.api.users.functions import get_user_by_email
from modules.api.auth.functions import find_refresh_token
from modules.api.auth.security import anonymize, hash_password, hash_token
from fastapi.responses import JSONResponse
from uuid import uuid4

load_dotenv()

# Configuration du logger
logger = configure_logger()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# Gestion de l'authentification avec OAuth2
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    scopes={
        "me": "Voir ses informations personnelles",
        "admin": "Accès aux opérations administratives",
    },
)

auth_router = APIRouter()


@auth_router.post(
    "/login",
    response_model=Token,
    summary="Connexion et génération d'un token JWT",
    description="Vérifie les informations de connexion et retourne "
    "un token d'authentification JWT si les identifiants sont corrects.",
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

    access_token_expires = timedelta(minutes=15)
    refresh_token_expires = timedelta(days=7)

    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.role},
        expires_delta=access_token_expires,
    )

    refresh_token = create_access_token(
        data={"sub": user.email, "type": "refresh"},
        expires_delta=refresh_token_expires,
    )

    # Sauvegarde en base
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


@auth_router.post(
    "/refresh",
    response_model=Token,
    summary="Rafraîchir un token JWT d'accès",
    description="Permet de générer un nouveau token d'accès à partir d'un token de rafraîchissement valide. "  # noqa
    "Le token de rafraîchissement doit contenir le type 'refresh' pour être accepté.",  # noqa
)
def refresh_token(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_users_db)
):
    # 🔐 Décode le token JWT
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

    # 🔍 Vérifie que le token existe bien en base
    hashed_token = hash_token(token)
    print("\n================ DEBUG /auth/refresh ================")
    print(" Token JWT reçu :", token)
    print(" Token hashé :", hashed_token)
    print(" Tous les tokens en base :")
    for rt in db.query(RefreshToken).all():
        print("-", rt.token)
    print("=====================================================\n")

    refresh_token_db = find_refresh_token(db, hashed_token)

    if not refresh_token_db:
        print("❌ Token introuvable dans la base.")
        raise HTTPException(status_code=401, detail="Refresh token introuvable")

    if refresh_token_db.expires_at.replace(tzinfo=timezone.utc) < datetime.now(
        timezone.utc
    ):
        print("⏳ Token expiré :", refresh_token_db.expires_at)
        raise HTTPException(status_code=401, detail="Refresh token expiré")

    print("✅ Token valide, on passe à la rotation...")

    # Révoquer l'ancien refresh token
    refresh_token_db.revoked = True

    # Récupère l'utilisateur en base via email anonymisé
    hashed_email = anonymize(email)
    user = get_user_by_email(hashed_email, db)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # Crée un nouveau access token
    new_access_token = create_access_token(
        data={"sub": email, "role": role}, expires_delta=timedelta(minutes=15)
    )

    # Crée un nouveau refresh token
    new_refresh_token = create_access_token(
        data={"sub": email, "role": role, "type": "refresh", "jti": str(uuid4())},
        expires_delta=timedelta(days=7),
    )
    hashed_new_refresh_token = hash_token(new_refresh_token)
    refresh_expiry = datetime.now(timezone.utc) + timedelta(days=7)

    store_refresh_token(
        db, user_id=user.id, token=hashed_new_refresh_token, expires_at=refresh_expiry
    )

    db.commit()

    return JSONResponse(
        {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
    )


@auth_router.get(
    "/users/me",
    response_model=UserResponse,
    summary="Récupérer les informations de l'utilisateur connecté",  # noqa
    description="Retourne les détails de l'utilisateur authentifié en utilisant son token.",  # noqa
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
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            role=user.role.role,
        )

    except JWTError as e:
        # Log d'erreur si le token est invalide ou expiré
        logger.error(f"Erreur de JWT: {str(e)}")
        raise credentials_exception


@auth_router.get(
    "/users/", response_model=list[UserResponse], summary="Lister tous les utilisateurs"
)
def get_all_users(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_users_db)
):
    """Seuls les administrateurs peuvent voir tous les utilisateurs."""

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")

        if role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Accès refusé : réservé aux administrateurs.",
            )

        return [
            UserResponse(
                id=u.id,
                name=u.name,
                email=u.email,
                is_active=u.is_active,
                role=u.role.role,
            )
            for u in db.query(User).all()
        ]

    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré.")


@auth_router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un utilisateur",
    description="Supprime un utilisateur spécifique en fonction de son ID.",
)
def delete_user(
    user_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_users_db),
):
    """Seuls les administrateurs peuvent supprimer un utilisateur."""

    try:
        # Décodage du token JWT pour obtenir l'email de l'utilisateur qui fait
        # la requête
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")

        # Vérifier que l'utilisateur est un admin
        if role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Accès refusé : réservé aux administrateurs.",
            )

        # Suppression de l'utilisateur
        user_to_delete = db.query(User).filter(User.id == user_id).first()
        if not user_to_delete:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")

        db.delete(user_to_delete)
        db.commit()

        return JSONResponse({"message": "Utilisateur supprimé"})

    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré.")


@auth_router.post(
    "/users/",
    response_model=UserResponse,
    summary="Créer un nouvel utilisateur",
    description="Ajoute un nouvel utilisateur à la base de données.",
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


@auth_router.patch(
    "/users/{user_id}/role",
    summary="Modifier le rôle d'un utilisateur",
    description="Permet à un administrateur de modifier le rôle d'un utilisateur.",  # noqa
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
        role = payload.get("role")

        if role != "admin":
            raise HTTPException(
                status_code=403, detail="Accès refusé : réservé aux administrateurs."
            )

        # Récupérer l'utilisateur cible
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=404, detail="Utilisateur à modifier non trouvé."
            )

        # Récupérer l'objet Role correspondant au nom
        new_role = db.query(Role).filter(Role.role == role_update.role).first()
        if not new_role:
            raise HTTPException(status_code=404, detail="Rôle non trouvé.")

        # Assigner le nouveau rôle
        user.role_id = new_role.id
        db.commit()
        db.refresh(user)

        return JSONResponse(
            {
                "message": f"Rôle de l'utilisateur mis à jour en '{new_role.role}'."
            }  # noqa
        )

    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré.")
