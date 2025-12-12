import sqlite3

def fix_sub_sources():
    conn = sqlite3.connect('discussions.db')
    cursor = conn.cursor()
    
    # Fix for Copilot for Small and Medium Business
    print("Updating sub_source for Copilot for Small and Medium Business...")
    cursor.execute("""
        UPDATE discussions 
        SET sub_source = 'copilotforsmallandmediumbusiness' 
        WHERE url LIKE '%/discussions/copilotforsmallandmediumbusiness/%'
    """)
    print(f"Updated {cursor.rowcount} rows to 'copilotforsmallandmediumbusiness'.")

    # Normalize generic "Microsoft 365 Copilot" to "microsoft365copilot"
    print("Updating remaining generic 'Microsoft 365 Copilot' to 'microsoft365copilot'...")
    cursor.execute("""
        UPDATE discussions
        SET sub_source = 'microsoft365copilot'
        WHERE sub_source = 'Microsoft 365 Copilot'
    """)
    print(f"Updated {cursor.rowcount} rows to 'microsoft365copilot'.")

    # Check final state
    cursor.execute("SELECT DISTINCT sub_source FROM discussions")
    print("Current sub_sources:", cursor.fetchall())

    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_sub_sources()
