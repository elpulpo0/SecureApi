from modules.database.session import Base
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
print("[DEBUG] PYTHONPATH =", sys.path)


def reset_test_db(engine):
    """Crée les mêmes tables dans une base temporaire en mémoire pour les tests."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
