import sqlite3
import pandas as pd
from werkzeug.security import generate_password_hash

# Function to insert data into the wheel_set table
def insert_users():
    # Connect to your SQLite database (adjust the path as necessary)
    conn = sqlite3.connect('carcraft.db')
    cursor = conn.cursor()

    # Open CSV file
    try:
        df = pd.read_csv("users.csv")
    except Exception as e:
        print(e)
        print("Users.csv not found. Quitting.")
        return

    # Load first 100 accounts
    df = df.head(100)
    for username in df['author']:
        email = f"{username}@gmail.com"
        password_hash = generate_password_hash("password")
        
        cursor.execute('''
            INSERT INTO user (username, email, password_hash, admin)
            VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, 0))

    # Insert admin accounts
    cursor.execute('''
        INSERT INTO user (username, email, password_hash, admin)
        VALUES (?, ?, ?, ?)
        ''', ("admin", "admin@admin.com", generate_password_hash("admin"), 1))
    
    print("User data successfully inserted!")
    conn.commit()
    # Close the database connection
    conn.close()
