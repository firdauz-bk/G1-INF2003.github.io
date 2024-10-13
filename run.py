import sqlite3
import pandas as pd

# Connect to the SQLite database
conn = sqlite3.connect('carcraft.db')
cursor = conn.cursor()

# SQL query
query = """
SELECT 
    'sqlite' AS dbms,
    m.tbl_name AS TABLE_NAME,
    p.name AS COLUMN_NAME,
    p.cid + 1 AS ORDINAL_POSITION,
    p.type AS DATA_TYPE,
    CASE WHEN p.type LIKE 'VARCHAR%' THEN CAST(SUBSTR(p.type, 9, LENGTH(p.type) - 9) AS INTEGER) ELSE NULL END AS CHARACTER_MAXIMUM_LENGTH,
    CASE 
        WHEN p.pk = 1 THEN 'PRIMARY KEY'
        WHEN fk.id IS NOT NULL THEN 'FOREIGN KEY'
        ELSE NULL
    END AS CONSTRAINT_TYPE,
    fk."table" AS REFERENCED_TABLE_NAME,
    fk."to" AS REFERENCED_COLUMN_NAME
FROM 
    sqlite_master m
LEFT JOIN 
    pragma_table_info(m.tbl_name) p ON m.tbl_name != p.cid
LEFT JOIN 
    pragma_foreign_key_list(m.tbl_name) fk ON p.name = fk."from"
WHERE 
    m.type = 'table' AND 
    m.tbl_name != 'sqlite_sequence' AND
    m.tbl_name NOT LIKE 'sqlite_%'
ORDER BY 
    m.tbl_name, p.cid
"""

# Execute the query and fetch results
cursor.execute(query)
results = cursor.fetchall()

# Convert results to a pandas DataFrame for easier viewing
columns = [desc[0] for desc in cursor.description]
df = pd.DataFrame(results, columns=columns)

# Close the database connection
conn.close()

# Display the results
print(df)

# Optionally, save to CSV
df.to_csv('carcraft_schema.csv', index=False)