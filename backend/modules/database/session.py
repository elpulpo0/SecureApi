from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from modules.database.config import USERS_DATABASE_URL

# from modules.database.config import SECOND_DB_DATABASE_URL

Base = declarative_base()


def create_session(database_url: str):
    engine = create_engine(
        database_url, connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    return engine, SessionLocal


users_engine, UsersSessionLocal = create_session(USERS_DATABASE_URL)
# second_db_engine, SecondDbSessionLocal = create_session(SECOND_DB_DATABASE_URL) # A modifier
