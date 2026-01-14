import scrapy
from datetime import datetime
from scrapy_playwright.page import PageMethod

class RedditSpider(scrapy.Spider):
    name = "reddit"
    allowed_domains = ["reddit.com"]
    
    def __init__(self, subreddits="microsoft,microsoft365", limit=50, *args, **kwargs):
        super(RedditSpider, self).__init__(*args, **kwargs)
        self.subreddits = subreddits.split(',')
        self.limit = int(limit)

    def start_requests(self):
        for subreddit in self.subreddits:
            url = f"https://www.reddit.com/r/{subreddit}/new/"
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "shreddit-post"),
                    ],
                },
                cb_kwargs={"subreddit": subreddit}
            )

    async def parse(self, response, subreddit):
        page = response.meta["playwright_page"]
        
        # Scroll to load more posts
        # We scroll a few times to trigger lazy loading
        # Each scroll waits a bit for content to populate
        for _ in range(5):
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000) 
            
        content = await page.content()
        await page.close()
        
        selector = scrapy.Selector(text=content)
        posts = selector.css("shreddit-post")
        
        self.logger.info(f"Found {len(posts)} posts for subreddit {subreddit}")
        
        for post in posts[:self.limit]:
            # Extract attributes from the custom element
            title = post.attrib.get("post-title")
            author = post.attrib.get("author")
            score = post.attrib.get("score")
            comment_count = post.attrib.get("comment-count")
            permalink = post.attrib.get("permalink")
            created_timestamp = post.attrib.get("created-timestamp")
            post_id = post.attrib.get("id")
            
            # Extract content from the text-body slot
            post_content = post.css("[slot='text-body'] ::text").getall()
            post_content = " ".join(post_content).strip() if post_content else ""

            discussion_url = f"https://www.reddit.com{permalink}"
            
            item = {
                "message_id": post_id,
                "title": title,
                "discussion_url": discussion_url,
                "author": author,
                "reply_count": int(comment_count) if comment_count else 0,
                "thumbs_up_count": int(score) if score else 0,
                "content": post_content,
                "publish_date": created_timestamp, 
                "replies": [], # Deep scraping skipped for no-API version
                "platform": "Reddit",
                "sub_source": subreddit
            }
            
            yield item
