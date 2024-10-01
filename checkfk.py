import sqlite3

# Connect to the database
conn = sqlite3.connect('carcraft.db')

# Create a cursor
cursor = conn.cursor()

# Check if foreign keys are enabled
cursor.execute("PRAGMA foreign_keys;")
print("Foreign Keys Enabled:", cursor.fetchone()[0])  # Should print 1 if enabled, 0 if not

# Enable foreign key support if not enabled
cursor.execute("PRAGMA foreign_keys = ON;")

# Check again to confirm
cursor.execute("PRAGMA foreign_keys;")
print("Foreign Keys Enabled:", cursor.fetchone()[0])  # Should print 1 after enabling

# Close the connection
conn.commit()
conn.close()
