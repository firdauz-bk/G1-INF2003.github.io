import sqlite3
import random

present_participles = ["Unending", "Freeing", "Alluring", "Losing", "Fleeing",
                      "Seering", "Jeering", "Leering", 'Worrying', "Willing"]

adjectives = ["Fast", "Exuberant", "Exemplary", "Wonderful", "Eldritch",
              "Terrible", "Ravenous", "Peculiar", "Graceful", "Radiant"]

nouns = ["Tempest", "Tangerine", "Codebreaker", "Salvation", "Judgement",
         "Nightmare", "Hatred", "Heretic", "Prophet", "Aegis"]

def insert_customizations():
    # Connect to your SQLite database (adjust the path as necessary)
    conn = sqlite3.connect('carcraft.db')
    cursor = conn.cursor()

    colors = cursor.execute("SELECT color.color_id FROM color").fetchall()
    wheel_sets = cursor.execute("SELECT wheel_set.wheel_id FROM wheel_set").fetchall()
    users = cursor.execute("SELECT user.user_id FROM user").fetchall()
    models = cursor.execute("SELECT model.model_id FROM model").fetchall()

    random.seed()

    # Generate customizations using models
    customization_count = 0
    for model in models:
        for color in colors:
            for wheel_set in wheel_sets:
                user_id = users[random.randint(0, len(users) - 1)][0]
                present_participle = present_participles[random.randint(0, len(present_participles) - 1)]
                adjective = adjectives[random.randint(0, len(adjectives) - 1)]
                noun = nouns[random.randint(0, len(nouns) - 1)]
                number = random.randint(0, 99)
                name = f"{present_participle} {adjective} {noun} IX{number:02d}"
                cursor.execute("""
                            INSERT INTO customization (user_id, model_id, color_id, wheel_id, customization_name)
                            VALUES(?, ?, ?, ?, ?)
                            """, (user_id, model[0], color[0], wheel_set[0], name))
                
                customization_count += 1

    print("Successfully inserted customizations.")            
    conn.commit()
    conn.close()
