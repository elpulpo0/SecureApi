from modules.api.users.create_db import init_users_db
from modules.api.main import create_app
import os

# Si on n'est pas en test, on initialise la base
if os.getenv("RUN_ENV") != "test":
    init_users_db()

app = create_app()
