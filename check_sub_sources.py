import sqlite3

def check_sub_sources():
    conn = sqlite3.connect('discussions.db')
    cursor = conn.cursor()
    
    print("--- Sub-sources for 'copilotforsmallandmediumbusiness' URLs ---")
    cursor.execute("SELECT sub_source, COUNT(*) FROM discussions WHERE url LIKE '%copilotforsmallandmediumbusiness%' GROUP BY sub_source")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
        
    print("\n--- All Sub-sources ---")
    cursor.execute("SELECT sub_source, COUNT(*) FROM discussions GROUP BY sub_source")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

    conn.close()

if __name__ == "__main__":
    check_sub_sources()
