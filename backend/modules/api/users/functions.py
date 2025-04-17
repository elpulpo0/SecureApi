from modules.api.users.create_db import User
from sqlalchemy.orm import Session


def get_user_by_email(email: str, db: Session):
    # Effectuer la recherche dans la base de données avec l'email anonymisé
    user = db.query(User).filter(User.email == email).first()

    return user
