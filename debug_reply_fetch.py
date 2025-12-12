import scrapy
import json
from customer_intent_scraper.spiders.techcommunity import TechcommunitySpider

class DebugReplyFetchSpider(TechcommunitySpider):
    name = "debug_reply_fetch"
    start_urls = ["https://techcommunity.microsoft.com"] # Dummy

    def start_requests(self):
        # We need headers first. So we use the standard start_requests to get headers.
        # But we want to trigger the API call for a specific ID after headers are captured.
        yield from super().start_requests()

    def parse(self, response):
        # This is called after headers are captured (if we use the standard logic)
        # But standard logic yields request to API list.
        # We want to override this to fetch a specific reply ID.
        
        # Capture headers logic is in capture_api_request, which sets self.api_headers.
        # But capture_api_request is an event handler.
        # The parse method is called when the page loads.
        
        # We need to wait for headers.
        # In TechcommunitySpider.parse:
        # if not self.api_headers: ... return
        
        # So we can reuse parse, but we need to inject our custom logic.
        
        # Let's copy the header extraction logic.
        if not self.api_headers:
            self.logger.error("Failed to capture API headers.")
            return

        # Extract cookies
        self.api_cookies = {}
        cookie_header = self.api_headers.get("cookie") or self.api_headers.get("Cookie")
        if cookie_header:
            for item in cookie_header.split(";"):
                if "=" in item:
                    k, v = item.strip().split("=", 1)
                    self.api_cookies[k] = v
        
        self.api_headers = {k: v for k, v in self.api_headers.items() if k.lower() not in ['content-length', 'host']}

        # Target Reply ID
        target_id = "message:4455122"
        
        self.logger.info(f"Fetching replies for target ID: {target_id}")
        
        yield scrapy.Request(
            url="https://techcommunity.microsoft.com/t5/s/api/2.1/graphql?opname=MessageReplies",
            method="POST",
            body=json.dumps(self.build_replies_payload(target_id, cursor=None)),
            headers=self.api_headers,
            cookies=self.api_cookies,
            callback=self.parse_debug_reply
        )

    def parse_debug_reply(self, response):
        data = json.loads(response.body)
        print(f"DEBUG: Response for {response.url}")
        print(json.dumps(data, indent=2))

