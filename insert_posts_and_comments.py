import sqlite3
import random

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

# Add the new categories
categories = ["help", "customization_showcase", "discussion"]

def insert_posts_and_comments(comment_count: int = 5):
    # Connect to your SQLite database (adjust the path as necessary)
    conn = sqlite3.connect('carcraft.db')
    cursor = conn.cursor()

    customizations = cursor.execute("SELECT customization.customization_id FROM customization").fetchall()
    users = cursor.execute("SELECT user.user_id, user.username FROM user").fetchall()

    # Generate Posts
    for user in users:
        category = categories[random.randint(0, len(categories) - 1)]  # Randomly select a category
        title = titles[random.randint(0, len(titles) - 1)]
        description = descriptions[random.randint(0, len(descriptions) - 1)]
        user_id = user[0]

        if category == "customization_showcase":
            if customizations:  # Check if there are any customizations
                customization_id = customizations[random.randint(0, len(customizations) - 1)][0]
                conn.execute("""
                            INSERT INTO post (title, description, user_id, customization_id, category)
                            VALUES(?, ?, ?, ?, ?)
                            """, (title, description, user_id, customization_id, category))
            else:
                # Fallback to another category if no customizations available
                category = random.choice([cat for cat in categories if cat != "customization_showcase"])
                conn.execute("""
                            INSERT INTO post (title, description, user_id, category)
                            VALUES(?, ?, ?, ?)
                            """, (title, description, user_id, category))
        else:
            conn.execute("""
                        INSERT INTO post (title, description, user_id, category)
                        VALUES(?, ?, ?, ?)
                        """, (title, description, user_id, category))

    # Generate Comments
    posts = cursor.execute("SELECT post.post_id FROM post").fetchall()

    for post in posts:
        post_id = post[0]
        for _ in range(0, comment_count):
            comment = comments[random.randint(0, len(comments) - 1)]
            user_id = users[random.randint(0, len(users) - 1)][0]
            conn.execute("""
                        INSERT INTO comment (content, user_id, post_id)
                        VALUES(?, ?, ?)
                        """, (comment, user_id, post_id))

    print("Successfully inserted posts and comments.")
    conn.commit()
    conn.close()
