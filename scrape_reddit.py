import praw
import sqlite3
import os
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RedditScraper:
    def __init__(self, client_id, client_secret, user_agent, db_name="discussions.db"):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.ensure_tables()

    def ensure_tables(self):
        # Same schema as the Scrapy pipeline
        self.cursor.execute("""
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
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.cursor.execute("""
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
        self.conn.commit()

    def scrape_subreddit(self, subreddit_name, limit=100, search_query=None):
        print(f"Scraping r/{subreddit_name}...")
        subreddit = self.reddit.subreddit(subreddit_name)
        
        if search_query:
            submissions = subreddit.search(search_query, limit=limit)
        else:
            submissions = subreddit.new(limit=limit)

        count = 0
        for submission in submissions:
            self.process_submission(submission, subreddit_name)
            count += 1
            if count % 10 == 0:
                print(f"Processed {count} posts...")
        
        print(f"Finished scraping {count} posts from r/{subreddit_name}.")

    def process_submission(self, submission, subreddit_name):
        # Insert Discussion
        try:
            publish_date = datetime.fromtimestamp(submission.created_utc).isoformat()
            
            self.cursor.execute("""
                INSERT OR REPLACE INTO discussions 
                (id, source_id, platform, sub_source, title, author, publish_date, content, url, reply_count, thumbs_up_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"reddit_{submission.id}",
                submission.id,
                "Reddit",
                subreddit_name,
                submission.title,
                str(submission.author),
                publish_date,
                submission.selftext,
                submission.url,
                submission.num_comments,
                submission.score
            ))

            # Process Comments (Replies)
            submission.comments.replace_more(limit=0) # Flatten comment tree, skip 'load more'
            for comment in submission.comments.list():
                comment_date = datetime.fromtimestamp(comment.created_utc).isoformat()
                
                self.cursor.execute("""
                    INSERT OR REPLACE INTO replies
                    (id, parent_id, author, publish_date, content, thumbs_up_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    f"reddit_{comment.id}",
                    f"reddit_{submission.id}",
                    str(comment.author),
                    comment_date,
                    comment.body,
                    comment.score
                ))
            
            self.conn.commit()
        except Exception as e:
            print(f"Error processing post {submission.id}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Scrape Reddit discussions to SQLite.")
    parser.add_argument("--subreddit", required=True, help="Subreddit to scrape (e.g., microsoft)")
    parser.add_argument("--query", help="Search query (optional)")
    parser.add_argument("--limit", type=int, default=50, help="Number of posts to scrape")
    args = parser.parse_args()

    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "script:customer_intent_scraper:v1.0 (by /u/yourusername)")

    if not client_id or not client_secret:
        print("Error: Missing REDDIT_CLIENT_ID or REDDIT_CLIENT_SECRET in .env file.")
        return

    scraper = RedditScraper(client_id, client_secret, user_agent)
    scraper.scrape_subreddit(args.subreddit, limit=args.limit, search_query=args.query)

if __name__ == "__main__":
    main()
