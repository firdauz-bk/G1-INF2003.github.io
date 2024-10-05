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

# Populate the tables with dummy data
insert_vehicle_types()
insert_brands()
insert_colors()
insert_wheel_sets()

print("Dummy data inserted successfully!")

# Close the database connection
conn.close()
