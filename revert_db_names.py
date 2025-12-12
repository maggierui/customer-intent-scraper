import sqlite3

DB_PATH = "discussions.db"

def revert_names():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Before revert:")
    print('Sub-sources:', [r[0] for r in cursor.execute('SELECT DISTINCT sub_source FROM discussions').fetchall()])
    
    # Fetch all rows
    rows = cursor.execute("SELECT id, url FROM discussions WHERE platform = 'Tech Community'").fetchall()
    
    updated_count = 0
    for row_id, url in rows:
        if not url:
            continue
            
        slug = None
        parts = url.split("/")
        
        if "t5" in parts:
            try:
                idx = parts.index("t5")
                slug = parts[idx+1]
            except:
                pass
        elif "category" in parts:
            try:
                idx = parts.index("category")
                slug = parts[idx+1]
            except:
                pass
        elif "discussions" in parts:
             # Handle https://techcommunity.microsoft.com/discussions/microsoft365copilot/...
             try:
                idx = parts.index("discussions")
                slug = parts[idx+1]
             except:
                pass

        if slug:
            cursor.execute("UPDATE discussions SET sub_source = ? WHERE id = ?", (slug, row_id))
            updated_count += 1

    conn.commit()
    
    print(f"\nUpdated {updated_count} rows.")
    print("\nAfter revert:")
    print('Sub-sources:', [r[0] for r in cursor.execute('SELECT DISTINCT sub_source FROM discussions').fetchall()])
    
    conn.close()

if __name__ == "__main__":
    revert_names()
