from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATABASE_DIR = BASE_DIR / "db"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

USERS_DATABASE_PATH = DATABASE_DIR / "users.db"
# SECOND_DB_DATABASE_PATH = DATABASE_DIR / "secondDb.db" # A modifier

USERS_DATABASE_URL = f"sqlite:///{USERS_DATABASE_PATH}"
# SECOND_DB_DATABASE_URL = f"sqlite:///{SECOND_DB_DATABASE_PATH}" # A modifier
