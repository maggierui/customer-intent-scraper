import sqlite3

conn = sqlite3.connect('discussions.db')
cursor = conn.cursor()

print("--- Analysis Counts by Sub-source ---")
cursor.execute("SELECT sub_source, COUNT(*) as total, COUNT(analysis_sentiment) as analyzed FROM discussions GROUP BY sub_source")
rows = cursor.fetchall()
for row in rows:
    print(f"Sub-source: {row[0]}, Total: {row[1]}, Analyzed: {row[2]}")

conn.close()
