from pymongo import MongoClient
from datetime import datetime
from python_init.createtables import regenerate_collections
from python_init.insert_fake_user import insert_users
from python_init.insert_customizations import insert_customizations
from python_init.insert_posts_and_comments import insert_posts_and_comments

# Dummy data for each collection
vehicle_types = [
    {"name": "Sedan"},
    {"name": "SUV"},
    {"name": "Sports"}
]

brands = [
    {"name": "Toyota"},
    {"name": "Honda"},
    {"name": "BMW"}
]

models = [
    {"name": "Civic", "brand_name": "Honda", "type_name": "Sports"},
    {"name": "GR86", "brand_name": "Toyota", "type_name": "Sports"},
    {"name": "M5", "brand_name": "BMW", "type_name": "Sedan"},
    {"name": "Prius", "brand_name": "Toyota", "type_name": "SUV"},
    {"name": "X7", "brand_name": "BMW", "type_name": "SUV"}
]

colors = [
    {"name": "Blue"},
    {"name": "White"}
]

wheel_sets = [
    {"name": "Alloy", "description": "Lightweight and stylish alloy wheels."},
    {"name": "Steel", "description": "Durable and budget-friendly steel wheels."}
]


# Functions to insert data into collections
def insert_vehicle_types(db):
    db["vehicle_type"].insert_many(vehicle_types)
    print("Vehicle types inserted.")


def insert_brands(db):
    db["brand"].insert_many(brands)
    print("Brands inserted.")


def insert_colors(db):
    db["color"].insert_many(colors)
    print("Colors inserted.")


def insert_wheel_sets(db):
    db["wheel_set"].insert_many(wheel_sets)
    print("Wheel sets inserted.")


def insert_models(db):
    vehicle_types_collection = db["vehicle_type"]
    brands_collection = db["brand"]

    model_data = []
    for model in models:
        # Resolve foreign keys
        type_doc = vehicle_types_collection.find_one({"name": model["type_name"]})
        brand_doc = brands_collection.find_one({"name": model["brand_name"]})

        model_data.append({
            "name": model["name"],
            "brand_id": brand_doc["_id"],
            "type_id": type_doc["_id"]
        })

    db["model"].insert_many(model_data)
    print("Models inserted.")


if __name__ == "__main__":
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017/")  # Replace with your MongoDB URI
    db = client["carcraft"]

    # Reset collections
    regenerate_collections(db)

    # Insert dummy data
    insert_vehicle_types(db)
    insert_brands(db)
    insert_colors(db)
    insert_wheel_sets(db)
    insert_models(db)

    print("Base dummy data inserted successfully!")

    # Insert additional data using predefined scripts
    insert_users(db)
    insert_customizations(db)
    inserted_customizations = db["customization"].count_documents({})
    print(f"Total customizations in database: {inserted_customizations}")

    insert_posts_and_comments(db)

    print("All dummy data inserted successfully!")