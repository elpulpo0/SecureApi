import os
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from utils.security import anonymize, hash_password
from utils.logger_config import configure_logger
from modules.api.users.models import User, Base
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
        create_first_users()
    else:
        logger.info(
            "La base de données 'users' existe déjà. Aucun changement nécessaire."
        )


def create_first_users():
    """Crée un administrateur et des éditeurs avec les informations du fichier .env."""
    db: Session = UsersSessionLocal()

    try:
        existing_admin = db.query(User).filter(User.role == "admin").first()
        if existing_admin:
            logger.info(
                "Un administrateur existe déjà. Aucune action nécessaire."
            )
            return

        # Récupération depuis le .env
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASSWORD")

        # Création des utilisateurs
        users = [
            User(
                email=anonymize(admin_email),
                password=hash_password(admin_password),
                role="admin",
                is_active=True,
            ),
        ]

        for user in users:
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(
                f"{user.role.capitalize()} {admin_email} créé avec succès."
            )

    except Exception as e:
        db.rollback()
        logger.error(
            f"Erreur lors de la création des utilisateurs initiaux : {e}"
        )

    finally:
        db.close()
