import pandas as pd
from werkzeug.security import generate_password_hash
from pymongo import MongoClient

def insert_users(db):
    """
    Inserts dummy users into the `users` collection in MongoDB.
    """
    # Open CSV file
    try:
        df = pd.read_csv("users.csv")
    except Exception as e:
        print(e)
        print("users.csv not found. Quitting.")
        return

    # Load first 100 accounts
    df = df.head(100)
    
    # Prepare users data
    users = []
    for username in df['author']:
        email = f"{username}@gmail.com"
        password_hash = generate_password_hash("password")
        user_data = {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "admin": False  # Default non-admin
        }
        users.append(user_data)

    # Insert users into the MongoDB collection
    try:
        db["users"].insert_many(users)
        print("User data successfully inserted!")
    except Exception as e:
        print(f"Error inserting user data: {e}")
    
    # Insert admin accounts
    admin_user = {
        "username": "admin",
        "email": "admin@admin.com",
        "password_hash": generate_password_hash("admin"),
        "admin": True
    }
    try:
        db["users"].insert_one(admin_user)
        print("Admin user successfully inserted!")
    except Exception as e:
        print(f"Error inserting admin user: {e}")

# Example MongoDB connection and insertion
if __name__ == "__main__":
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client["carcraft_db"]  # Your database name here
    
    insert_users(db)  # Call the function to insert users
