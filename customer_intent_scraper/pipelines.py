# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import re
from itemadapter import ItemAdapter


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
            cleaned_replies = []
            for reply in replies:
                if isinstance(reply, dict):
                    # Clean each string value in the reply dictionary
                    clean_reply = {
                        k: self.clean_text(v) if isinstance(v, str) else v 
                        for k, v in reply.items()
                    }
                    
                    # Filter out empty or useless replies if needed
                    if self.is_valid_reply(clean_reply):
                        cleaned_replies.append(clean_reply)
            
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
