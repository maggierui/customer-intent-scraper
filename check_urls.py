import sqlite3

conn = sqlite3.connect('discussions.db')
cursor = conn.cursor()

print("--- URLs for 'Microsoft 365 Copilot' ---")
cursor.execute("SELECT url FROM discussions WHERE sub_source = 'Microsoft 365 Copilot' LIMIT 5")
rows = cursor.fetchall()
for row in rows:
    print(row[0])

print("\n--- URLs for 'microsoft365copilot' ---")
cursor.execute("SELECT url FROM discussions WHERE sub_source = 'microsoft365copilot' LIMIT 5")
rows = cursor.fetchall()
for row in rows:
    print(row[0])

conn.close()
