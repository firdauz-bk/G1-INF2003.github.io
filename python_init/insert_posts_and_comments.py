import random
from pymongo import MongoClient

# Define the lists for generating posts and comments
titles = ["Amazing!", "Incredible!", "Spectacular!", "Splendorific!", "Wonderful!",
          "Terrible!", "Disappointing!", "Failure!", "WTF!", "Stop.", "Why?"]

descriptions = ["I am very impressed.", "This is extremely whelming!", "I think you tried your best.", "A for effort.", "NOOOOOOOOOOOOOOOOOOOOO!",
                "This is an affront to existence!", "Please put in more effort.", "Why do you insist on releasing garbage.", "I hate software engineering!",
                "なにこれただのゴミじゃん！", "神車だ！！！！！", "What the heck is this?", "Please apply yourself.", "You have to keep the pedagogy in mind.",
                "I approve of this!", "I disapprove of this!", "一番推しのは小鞠だ"]

comments = ["Good post", "bump", "nice opinion", "you are wrong", "you should be ashamed of yourself",
            "this post is terrible", "kys", "what the heck are you talking about.", "this is terrible",
            "You should apologize to your parents for making this post.", "upvote", "I love the color red!",
            "Blue is a nice color", "You have yeed your last haw!", "My timbers have been shivered!", "Wow!", "しかのこのこのここしたんたん", "repost",
            "you should try using the search bar", "なにそれ草", "wwwwwwwwww", "マジ死ね"]

categories = ["help", "customization_showcase", "discussion"]

def insert_posts_and_comments(db, comment_count: int = 5):
    """
    Inserts dummy posts and comments into the `posts` and `comments` collections in MongoDB.
    """
    # Fetch necessary data from MongoDB collections (equivalent of SELECT queries)
    customizations = db["customization"].find({}, {"customization_id": 1})
    users = db["user"].find({}, {"user_id": 1, "username": 1})

    # Generate Posts
    for user in users:
        category = random.choice(categories)  # Randomly select a category
        title = random.choice(titles)
        description = random.choice(descriptions)
        user_id = user["user_id"]

        if category == "customization_showcase":
            if customizations.count() > 0:  # Check if there are any customizations
                customization = random.choice(list(customizations))  # Randomly pick a customization
                customization_id = customization["customization_id"]
                post = {
                    "title": title,
                    "description": description,
                    "user_id": user_id,
                    "customization_id": customization_id,
                    "category": category
                }
            else:
                # Fallback to another category if no customizations available
                category = random.choice([cat for cat in categories if cat != "customization_showcase"])
                post = {
                    "title": title,
                    "description": description,
                    "user_id": user_id,
                    "category": category
                }
        else:
            post = {
                "title": title,
                "description": description,
                "user_id": user_id,
                "category": category
            }
        
        # Insert the post into the MongoDB collection
        db["post"].insert_one(post)

    # Generate Comments
    posts = db["post"].find({}, {"post_id": 1})

    for post in posts:
        post_id = post["post_id"]
        for _ in range(comment_count):
            comment = random.choice(comments)
            user = random.choice(list(users))  # Randomly pick a user
            user_id = user["user_id"]
            comment_document = {
                "content": comment,
                "user_id": user_id,
                "post_id": post_id
            }
            # Insert the comment into the MongoDB collection
            db["comment"].insert_one(comment_document)

    print("Successfully inserted posts and comments.")

# Example MongoDB connection and insertion
if __name__ == "__main__":
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client["carcraft_db"]  # Your database name here
    
    insert_posts_and_comments(db)  # Call the function to insert posts and comments
