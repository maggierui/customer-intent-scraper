import sqlite3

db_path = 'discussions.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check count
cursor.execute("SELECT COUNT(*) FROM discussions WHERE analysis_author_role = 'IT Professional'")
count = cursor.fetchone()[0]
print(f"Found {count} rows with 'IT Professional'")

if count > 0:
    print("Updating rows to 'IT Admin'...")
    cursor.execute("UPDATE discussions SET analysis_author_role = 'IT Admin' WHERE analysis_author_role = 'IT Professional'")
    conn.commit()
    print("Update complete.")
    
    cursor.execute("SELECT COUNT(*) FROM discussions WHERE analysis_author_role = 'IT Professional'")
    new_count = cursor.fetchone()[0]
    print(f"Remaining 'IT Professional' rows: {new_count}")
else:
    print("No rows to update.")

conn.close()
