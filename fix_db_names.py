import sqlite3

DB_PATH = "discussions.db"

def fix_names():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Before update:")
    print('Platforms:', [r[0] for r in cursor.execute('SELECT DISTINCT platform FROM discussions').fetchall()])
    print('Sub-sources:', [r[0] for r in cursor.execute('SELECT DISTINCT sub_source FROM discussions').fetchall()])
    
    # Fix Platform
    cursor.execute("UPDATE discussions SET platform = 'Tech Community' WHERE platform = 'TechCommunity'")
    print(f"Updated {cursor.rowcount} rows for platform.")
    
    # Fix Sub-source
    cursor.execute("UPDATE discussions SET sub_source = 'Microsoft 365 Copilot' WHERE sub_source = 'microsoft365copilot'")
    print(f"Updated {cursor.rowcount} rows for sub_source (microsoft365copilot).")

    cursor.execute("UPDATE discussions SET sub_source = 'Microsoft 365 Copilot' WHERE sub_source = 'microsoft-365-copilot'")
    print(f"Updated {cursor.rowcount} rows for sub_source (microsoft-365-copilot).")
    
    cursor.execute("UPDATE discussions SET sub_source = 'Copilot for Small and Medium Business' WHERE sub_source = 'copilot-for-small-and-medium-business'")
    print(f"Updated {cursor.rowcount} rows for sub_source (copilot-for-small-and-medium-business).")
    
    conn.commit()
    
    print("\nAfter update:")
    print('Platforms:', [r[0] for r in cursor.execute('SELECT DISTINCT platform FROM discussions').fetchall()])
    print('Sub-sources:', [r[0] for r in cursor.execute('SELECT DISTINCT sub_source FROM discussions').fetchall()])
    
    conn.close()

if __name__ == "__main__":
    fix_names()
