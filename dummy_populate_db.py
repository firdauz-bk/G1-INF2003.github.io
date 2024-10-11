import sqlite3
from createtables import regenerate_tables
from insert_fake_user import insert_users
from insert_customizations import insert_customizations
from insert_posts_and_comments import insert_posts_and_comments


# Define dummy data for each table
vehicle_types = [
    ('Sedan',),
    ('SUV',),
    ('Sports',)
]

brands = [
    ('Toyota',),
    ('Honda',),
    ('BMW',)
]

models = [
    ('Civic', 'Honda', 'Sports',),
    ('GR86', 'Toyota', 'Sports',),
    ('M5', 'BMW', 'Sedan',),
    ('Prius', 'Toyota', 'SUV',)
]

colors = [
    ('Blue',),
    ('White',)
]

wheel_sets = [
    ('Alloy', 'Lightweight and stylish alloy wheels.',),
    ('Steel', 'Durable and budget-friendly steel wheels.',)
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

def insert_models():
    for model in models:
        cursor.execute(f"""
                        SELECT brand_id 
                        FROM brand
                        WHERE name = '{model[1]}'
                        """)
        brand_id = cursor.fetchone()[0]
        
        cursor.execute(f"""
                        SELECT type_id 
                        FROM vehicle_type
                        WHERE name = '{model[2]}'
                        """)
        type_id = cursor.fetchone()[0]
        
        name = model[0]
        cursor.execute("""
                       INSERT INTO model (name, brand_id, type_id)
                       VALUES (?, ?, ?)
                       """, 
                       (name, brand_id, type_id))
        
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
    insert_models()


    print("Dummy data inserted successfully!")

    insert_users()
    insert_customizations()
    insert_posts_and_comments()

    # Close the database connection
    conn.close()
