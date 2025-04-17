from modules.api.users.models import User, RefreshToken, Role
from modules.database.session import Base
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
print("[DEBUG] PYTHONPATH =", sys.path)


def init_test_db(engine):
    _ = [User, RefreshToken, Role]
    Base.metadata.create_all(bind=engine)
    print("🧪 Tables SQLAlchemy connues :", list(Base.metadata.tables.keys()))
