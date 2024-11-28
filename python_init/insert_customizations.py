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
    colors = list(db["color"].find({}, {"_id": 1}))  # Check if the field is `color_id`
    wheel_sets = list(db["wheel_set"].find({}, {"_id": 1}))  # Check if it's `wheel_set_id`
    users = list(db["user"].find({}, {"_id": 1}))  # Ensure it's `user_id`
    models = list(db["model"].find({}, {"_id": 1}))  # Ensure it's `model_id`

    if not colors or not wheel_sets or not users or not models:
        print("One or more collections are empty. Exiting.")
        return

    random.seed(42)  # Set a seed for reproducibility

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
                    "user_id": user["_id"],  # Assuming this is the correct field name
                    "model_id": model["_id"],  # Assuming this is the correct field name
                    "color_id": color["_id"],  # Assuming this is the correct field name
                    "wheel_set_id": wheel_set["_id"],  # Assuming this is the correct field name
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
    db = client["carcraft"]  # Your database name here
    
    insert_customizations(db)  # Call the function to insert customizations
