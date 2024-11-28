def insert_users(db):
    """
    Inserts dummy users into the `users` collection.
    """
    users = [
        {"username": "admin", "email": "admin@example.com", "password_hash": "hashed_password", "admin": True},
        {"username": "user1", "email": "user1@example.com", "password_hash": "hashed_password1", "admin": False},
        {"username": "user2", "email": "user2@example.com", "password_hash": "hashed_password2", "admin": False}
    ]
    db["user"].insert_many(users)
    print("Dummy users inserted successfully.")
