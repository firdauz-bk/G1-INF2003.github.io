import sqlite3
from createtables import regenerate_tables
from insert_fake_user import insert_users
from insert_models import insert_models
from insert_customizations import insert_customizations
from insert_posts_and_comments import insert_posts_and_comments


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

if __name__ == "__main__":
    # Connect to your SQLite database (adjust the path as necessary)
    conn = sqlite3.connect('carcraft.db')
    cursor = conn.cursor()

    # Resets all the Tables
    regenerate_tables()

    # Populate the tables with dummy data
    insert_vehicle_types()
    insert_brands()
    insert_colors()
    insert_wheel_sets()

    print("Dummy data inserted successfully!")

    insert_users()
    insert_models()
    insert_customizations()
    insert_posts_and_comments()

    # Close the database connection
    conn.close()
