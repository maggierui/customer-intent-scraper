import sqlite3

def check_counts():
    conn = sqlite3.connect('discussions.db')
    cursor = conn.cursor()
    
    # Count discussions for the specific board
    cursor.execute("SELECT COUNT(*) FROM discussions WHERE url LIKE '%copilotforsmallandmediumbusiness%'")
    discussion_count = cursor.fetchone()[0]
    
    # Sum of reply counts reported in discussions for the specific board
    cursor.execute("SELECT SUM(reply_count) FROM discussions WHERE url LIKE '%copilotforsmallandmediumbusiness%'")
    total_replies_reported = cursor.fetchone()[0]
    
    # Count actual replies stored (joined with discussions)
    cursor.execute("""
        SELECT COUNT(*) FROM replies r
        JOIN discussions d ON r.parent_id = d.id
        WHERE d.url LIKE '%copilotforsmallandmediumbusiness%'
    """)
    stored_replies_count = cursor.fetchone()[0]
    
    print(f"Discussions (copilotforsmallandmediumbusiness): {discussion_count}")
    print(f"Total Replies (Reported): {total_replies_reported}")
    print(f"Total Replies (Stored): {stored_replies_count}")
    print(f"Total Messages (Discussions + Reported Replies): {discussion_count + (total_replies_reported or 0)}")
    
    conn.close()

if __name__ == "__main__":
    check_counts()
