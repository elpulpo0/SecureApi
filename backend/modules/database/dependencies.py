from modules.database.session import UsersSessionLocal
# from modules.database.session import SecondDbSessionLocal  # A modifier


def get_users_db():
    db = UsersSessionLocal()
    try:
        yield db
    finally:
        db.close()


# def get_second_db_db():  # A modifier
#     db = SecondDbSessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
