import random
from pymongo import MongoClient

# Define the lists for generating customizations
present_participles = ["Unending", "Freeing", "Alluring", "Losing", "Fleeing",
                       "Seering", "Jeering", "Leering", 'Worrying', "Willing"]

adjectives = ["Fast", "Exuberant", "Exemplary", "Wonderful", "Eldritch",
              "Terrible", "Ravenous", "Peculiar", "Graceful", "Radiant"]

nouns = ["Tempest", "Tangerine", "Codebreaker", "Salvation", "Judgement",
         "Nightmare", "Hatred", "Heretic", "Prophet", "Aegis"]

def insert_customizations(db):
    """
    Inserts dummy customizations into the `customizations` collection in MongoDB.
    """
    # Fetch data from MongoDB collections (equivalent of SELECT queries)
    colors = db["color"].find({}, {"color_id": 1})
    wheel_sets = db["wheel_set"].find({}, {"wheel_id": 1})
    users = db["user"].find({}, {"user_id": 1})
    models = db["model"].find({}, {"model_id": 1})

    random.seed()

    # Generate customizations using models
    customization_count = 0
    for model in models:
        for color in colors:
            for wheel_set in wheel_sets:
                user = random.choice(users)  # Randomly pick a user
                present_participle = random.choice(present_participles)
                adjective = random.choice(adjectives)
                noun = random.choice(nouns)
                number = random.randint(0, 99)
                name = f"{present_participle} {adjective} {noun} IX{number:02d}"

                # Create the customization document
                customization = {
                    "user_id": user["user_id"],
                    "model_id": model["model_id"],
                    "color_id": color["color_id"],
                    "wheel_id": wheel_set["wheel_id"],
                    "customization_name": name
                }

                # Insert the customization into the MongoDB collection
                try:
                    db["customization"].insert_one(customization)
                    customization_count += 1
                except Exception as e:
                    print(f"Error inserting customization: {e}")

    print(f"Successfully inserted {customization_count} customizations.")

# Example MongoDB connection and insertion
if __name__ == "__main__":
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client["carcraft_db"]  # Your database name here
    
    insert_customizations(db)  # Call the function to insert customizations
