import sqlite3
import pandas as pd
from werkzeug.security import generate_password_hash

# Connect to your SQLite database (adjust the path as necessary)
conn = sqlite3.connect('carcraft.db')
cursor = conn.cursor()

# Define dummy data for each table
vehicle_types = [
    ('Sedan',),
    ('SUV',)
]

brands = [
    ('Toyota',),
    ('Honda',)
]

colors = [
    ('Red',),
    ('Blue',)
]

wheel_sets = [
    ('Alloy Wheels', 'Lightweight and stylish alloy wheels.'),
    ('Steel Wheels', 'Durable and budget-friendly steel wheels.')
]

# Function to insert data into the vehicle_type table
def insert_vehicle_types():
    cursor.executemany('INSERT INTO vehicle_type (name) VALUES (?)', vehicle_types)
    conn.commit()

# Function to insert data into the brand table
def insert_brands():
    cursor.executemany('INSERT INTO brand (name) VALUES (?)', brands)
    conn.commit()

# Function to insert data into the color table
def insert_colors():
    cursor.executemany('INSERT INTO color (name) VALUES (?)', colors)
    conn.commit()

# Function to insert data into the wheel_set table
def insert_wheel_sets():
    cursor.executemany('INSERT INTO wheel_set (name, description) VALUES (?, ?)', wheel_sets)
    conn.commit()

# Function to insert data into the wheel_set table
def insert_users():
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
    
    conn.commit()


# Populate the tables with dummy data
insert_vehicle_types()
insert_brands()
insert_colors()
insert_wheel_sets()
insert_users()

print("Dummy data inserted successfully!")

# Close the database connection
conn.close()
