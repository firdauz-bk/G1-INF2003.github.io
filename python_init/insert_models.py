import sqlite3

def insert_models():
    # Connect to your SQLite database (adjust the path as necessary)
    conn = sqlite3.connect('carcraft.db')
    cursor = conn.cursor()

    vehicle_types = cursor.execute("SELECT vehicle_type.name FROM vehicle_type").fetchall()
    brands = cursor.execute("SELECT brand.name FROM brand").fetchall()

    # Create new models using vehicle types
    for vehicle_type in vehicle_types:
        for brand in brands:
            name = f"{brand[0]} {vehicle_type[0]}"
            conn.execute('''
                        INSERT INTO model (brand_id, type_id, name)
                        VALUES(?, ?, ?)
                        ''', (brand[0], vehicle_type[0], name))

    print("Successfully inserted models.")
    conn.commit()
    conn.close()