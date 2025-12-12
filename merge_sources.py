import sqlite3

def merge_sources():
    conn = sqlite3.connect('discussions.db')
    cursor = conn.cursor()

    print("Merging 'Microsoft 365 Copilot' into 'microsoft365copilot'...")
    
    # Check counts before
    cursor.execute("SELECT sub_source, COUNT(*) FROM discussions GROUP BY sub_source")
    print("Counts before merge:", cursor.fetchall())

    # Update
    cursor.execute("""
        UPDATE discussions
        SET sub_source = 'microsoft365copilot'
        WHERE sub_source = 'Microsoft 365 Copilot'
    """)
    print(f"Updated {cursor.rowcount} rows.")

    # Check counts after
    cursor.execute("SELECT sub_source, COUNT(*) FROM discussions GROUP BY sub_source")
    print("Counts after merge:", cursor.fetchall())

    conn.commit()
    conn.close()

if __name__ == "__main__":
    merge_sources()
