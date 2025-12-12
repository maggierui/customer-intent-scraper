# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


import sqlite3
import json
import os
import re
from itemadapter import ItemAdapter
import logging
import scrapy

class SQLitePipeline:
    def __init__(self, db_name="discussions.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            db_name=crawler.settings.get("SQLITE_DB_NAME", "discussions.db")
        )

    def open_spider(self, spider):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def close_spider(self, spider):
        if self.conn:
            self.conn.commit()
            self.conn.close()

    def create_tables(self):
        # Main discussions table
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
        
        # Replies table
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

    def process_item(self, item, spider):
        # Determine platform and sub_source
        platform = "Tech Community" 
        sub_source = "microsoft365copilot" # Default
        
        # Extract sub_source from URL if possible
        if "techcommunity.microsoft.com" in item.get("discussion_url", ""):
            parts = item["discussion_url"].split("/")
            # Check for /t5/slug/ or /category/slug/
            slug = None
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
                try:
                    idx = parts.index("discussions")
                    slug = parts[idx+1]
                except:
                    pass
            
            if slug:
                # Use the raw slug as the sub_source
                sub_source = slug

        # Insert Discussion
        try:
            self.cursor.execute("""
                INSERT OR REPLACE INTO discussions 
                (id, source_id, platform, sub_source, title, author, publish_date, content, url, reply_count, thumbs_up_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get("message_id"),
                item.get("message_id"), # source_id same as message_id for now
                platform,
                sub_source,
                item.get("title"),
                item.get("author"),
                item.get("publish_date"),
                item.get("content"),
                item.get("discussion_url"),
                item.get("reply_count", 0),
                item.get("thumbs_up_count", 0)
            ))
            
            # Insert Replies
            if "replies" in item and item["replies"]:
                for reply in item["replies"]:
                    self.cursor.execute("""
                        INSERT OR REPLACE INTO replies
                        (id, parent_id, author, publish_date, content, thumbs_up_count)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        reply.get("id"),
                        item.get("message_id"),
                        reply.get("author"),
                        reply.get("publish_date"),
                        reply.get("content"),
                        reply.get("thumbs_up_count", 0)
                    ))
            
            self.conn.commit()
            
        except sqlite3.Error as e:
            spider.logger.error(f"Database error: {e}")
            
        return item

class CustomerIntentScraperPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # 1. Clean top-level string fields
        for field_name in adapter.field_names():
            value = adapter.get(field_name)
            if isinstance(value, str):
                adapter[field_name] = self.clean_text(value)
        
        # 2. Clean nested 'replies' list
        replies = adapter.get('replies')
        if replies and isinstance(replies, list):
            logging.info(f"Pipeline received {len(replies)} replies")
            cleaned_replies = []
            for reply in replies:
                if isinstance(reply, (dict, scrapy.Item)):
                    # Clean each string value in the reply dictionary
                    # For scrapy.Item, we need to be careful about modification
                    if isinstance(reply, scrapy.Item):
                        reply_dict = dict(reply)
                    else:
                        reply_dict = reply
                        
                    clean_reply = {
                        k: self.clean_text(v) if isinstance(v, str) else v 
                        for k, v in reply_dict.items()
                    }
                    
                    # Filter out empty or useless replies if needed
                    if self.is_valid_reply(clean_reply):
                        cleaned_replies.append(clean_reply)
                    else:
                        logging.info(f"DEBUG: Dropped invalid reply: {clean_reply}")
                else:
                     logging.warning(f"Skipping reply of type {type(reply)}")
            
            logging.info(f"Pipeline keeping {len(cleaned_replies)} replies")
            adapter['replies'] = cleaned_replies

        return item

    def clean_text(self, text):
        if not text:
            return text
        # Replace multiple whitespace/newlines with single space
        text = re.sub(r'\s+', ' ', text)
        # Strip leading/trailing whitespace
        return text.strip()

    def is_valid_reply(self, reply):
        # Example filter: ignore replies with no content
        content = reply.get('content', '')
        if not content:
            return False
        return True
