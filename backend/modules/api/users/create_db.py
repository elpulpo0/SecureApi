import os
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from utils.security import anonymize, hash_password
from utils.logger_config import configure_logger
from modules.api.users.models import User, Base, Role
from modules.database.config import USERS_DATABASE_PATH
from modules.database.session import users_engine, UsersSessionLocal

# Configuration du logger
logger = configure_logger()

# Charger les variables d'environnement
load_dotenv()


def init_users_db():
    """Vérifie si la base de données existe et crée l'admin si besoin."""
    db_exists = USERS_DATABASE_PATH.exists()

    if not db_exists:
        logger.info(
            "La base de données 'users' n'existe pas. Création en cours..."
        )
        Base.metadata.create_all(bind=users_engine)
        logger.info("Base de données 'users' créée avec succès.")
        create_roles_and_first_users()
    else:
        logger.info(
            "La base de données 'users' existe déjà. Aucun changement nécessaire."  # noqa
        )


def create_roles_and_first_users():
    db: Session = UsersSessionLocal()

    try:
        # Création des rôles s'ils n'existent pas déjà
        default_roles = ["admin", "reader"]
        for role_name in default_roles:
            role = db.query(Role).filter_by(role=role_name).first()
            if not role:
                db.add(Role(role=role_name))
        db.commit()

        # Vérifier si un admin existe déjà
        admin_role = db.query(Role).filter_by(role="admin").first()
        if not admin_role:
            raise ValueError("Le rôle 'admin' n'existe pas")

        existing_admin = db.query(User).filter(User.role_id == admin_role.id).first()  # noqa
        if existing_admin:
            logger.info("Un administrateur existe déjà. Aucune action nécessaire.")  # noqa
            return

        # Récupération depuis le .env
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASSWORD")

        # Création du premier utilisateur admin
        admin_user = User(
            email=anonymize(admin_email),
            password=hash_password(admin_password),
            role_id=admin_role.id,
            is_active=True,
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        logger.info(f"Admin {admin_email} créé avec succès.")

    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors de l'initialisation : {e}")

    finally:
        db.close()
