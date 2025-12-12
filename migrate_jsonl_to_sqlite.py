import json
import sqlite3
import re
from datetime import datetime

DB_PATH = "discussions.db"
JSONL_PATH = "all_discussions_backup.jsonl"

def get_id_from_url(url):
    match = re.search(r'/(\d+)$', url)
    if match:
        return match.group(1)
    return None

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ensure tables exist (just in case)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS discussions (
            id TEXT PRIMARY KEY,
            source_id TEXT,
            platform TEXT,
            sub_source TEXT,
            title TEXT,
            author TEXT,
            publish_date TEXT,
            content TEXT,
            url TEXT,
            reply_count INTEGER,
            thumbs_up_count INTEGER,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            analysis_category TEXT,
            analysis_product_area TEXT,
            analysis_sentiment TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS replies (
            id TEXT PRIMARY KEY,
            parent_id TEXT,
            author TEXT,
            publish_date TEXT,
            content TEXT,
            thumbs_up_count INTEGER,
            FOREIGN KEY(parent_id) REFERENCES discussions(id)
        )
    """)
    
    count_discussions = 0
    count_replies = 0
    
    with open(JSONL_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                item = json.loads(line)
                
                url = item.get('discussion_url', '')
                source_id = get_id_from_url(url)
                
                if not source_id:
                    # Fallback if URL doesn't match expected pattern
                    source_id = str(hash(url))
                
                discussion_id = f"message:{source_id}"
                
                # Insert Discussion
                cursor.execute("""
                    INSERT OR IGNORE INTO discussions 
                    (id, source_id, platform, sub_source, title, author, publish_date, content, url, reply_count, thumbs_up_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    discussion_id,
                    source_id,
                    "Tech Community",
                    "Microsoft 365 Copilot", # Defaulting to this based on file context
                    item.get('title'),
                    item.get('author'),
                    item.get('publish_date'),
                    item.get('content'),
                    url,
                    item.get('reply_count', 0),
                    item.get('thumbs_up_count', 0)
                ))
                
                if cursor.rowcount > 0:
                    count_discussions += 1
                
                # Insert Replies
                replies = item.get('replies', [])
                if replies:
                    for reply in replies:
                        reply_id = reply.get('id')
                        if not reply_id:
                            # Generate a reply ID if missing
                            reply_id = f"{discussion_id}_reply_{hash(reply.get('content', ''))}"
                        
                        cursor.execute("""
                            INSERT OR IGNORE INTO replies
                            (id, parent_id, author, publish_date, content, thumbs_up_count)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            reply_id,
                            discussion_id,
                            reply.get('author'),
                            reply.get('publish_date'),
                            reply.get('content'),
                            reply.get('thumbs_up_count', 0)
                        ))
                        if cursor.rowcount > 0:
                            count_replies += 1
                            
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON line")
            except Exception as e:
                print(f"Error processing line: {e}")

    conn.commit()
    conn.close()
    print(f"Migration complete.")
    print(f"Imported {count_discussions} new discussions.")
    print(f"Imported {count_replies} new replies.")

if __name__ == "__main__":
    migrate()
