import scrapy
import json
import os
import asyncio
import sys
import re

# Fix for Windows Event Loop Policy
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from scrapy_playwright.page import PageMethod
from customer_intent_scraper.pages.techcommunity_microsoft_com import TechcommunityMicrosoftComDiscussionItemPage
from customer_intent_scraper.handlers import handle_graphql_response

class TechcommunitySpider(scrapy.Spider):
    name = "techcommunity"
    allowed_domains = ["techcommunity.microsoft.com"]
    start_urls = ["https://techcommunity.microsoft.com/category/microsoft365copilot/discussions/microsoft365copilot"]
    def __init__(self, *args, **kwargs):
        super(TechcommunitySpider, self).__init__(*args, **kwargs)
        self.seen_links = set()
        self.previous_links = set()
        self.api_headers = None
        self.api_cookies = None
        
        # Load previously scraped links to avoid re-crawling
        if os.path.exists("all_discussions.jsonl"):
            try:
                with open("all_discussions.jsonl", "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            item = json.loads(line)
                            if "discussion_url" in item:
                                self.previous_links.add(item["discussion_url"])
                        except:
                            pass
                self.logger.info(f"Loaded {len(self.previous_links)} previously scraped links.")
            except Exception as e:
                self.logger.warning(f"Could not load previous links: {e}")

    def capture_api_request(self, request):
        if "graphql" in request.url and request.method == "POST":
            self.logger.info(f"Capturing headers from: {request.url}")
            self.api_headers = request.headers
            self.logger.info("Captured API headers via event handler.")

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_event_handlers": {
                        "request": self.capture_api_request,
                    },
                    "playwright_page_methods": [
                        PageMethod("wait_for_timeout", 10000), # Wait for initial requests
                    ],
                },
                callback=self.parse
            )

    def build_payload(self, cursor=None):
        return {
            "operationName": "MessageViewsForWidget",
            "variables": {
                "useAvatar": True, "useAuthorRank": True, "useBody": True, "useTextBody": True,
                "useKudosCount": True, "useTimeToRead": True, "useMedia": True, "useReadOnlyIcon": True,
                "useRepliesCount": True, "useSearchSnippet": False, "useSolvedBadge": True,
                "useFullPageInfo": False, "useTags": True, "tagsFirst": 10, "tagsAfter": None,
                "truncateBodyLength": -1, "useSpoilerFreeBody": True, "removeTocMarkup": True,
                "usePreviewSubjectModal": False, "useOccasionData": False, "useMessageStatus": False,
                "removeProcessingText": True, "useUnreadCount": False, 
                "first": 50,
                "constraints": {
                    "boardId": {"eq": "board:Microsoft365Copilot"},
                    "depth": {"eq": 0},
                    "conversationStyle": {"eq": "FORUM"}
                },
                "sorts": {"conversationLastPostingActivityTime": {"direction": "DESC"}},
                "after": cursor,
                "before": None,
                "last": None
            },
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "9e08d498b0a03960a32846316b983adc71a637e2133124196f0073e35b521495"
                }
            }
        }

    async def parse(self, response):
        # page = response.meta.get("playwright_page")
        # if page:
        #     await page.close()

        if not self.api_headers:
            self.logger.error("Failed to capture API headers via event handler.")
            return

        # Extract cookies from captured headers
        self.api_cookies = {}
        cookie_header = self.api_headers.get("cookie") or self.api_headers.get("Cookie")
        if cookie_header:
            for item in cookie_header.split(";"):
                if "=" in item:
                    k, v = item.strip().split("=", 1)
                    self.api_cookies[k] = v
            self.logger.info(f"Successfully parsed {len(self.api_cookies)} cookies from captured headers.")
            self.logger.info("Parsed cookies from captured API headers.")
        else:
            self.logger.warning("No cookies found in captured API headers.")

        # Filter headers
        self.api_headers = {k: v for k, v in self.api_headers.items() if k.lower() not in ['content-length', 'host']}

        self.logger.info("Captured API headers and cookies. Switching to API mode.")
        
        # Start API loop
        yield scrapy.Request(
            url="https://techcommunity.microsoft.com/t5/s/api/2.1/graphql?opname=MessageViewsForWidget",
            method="POST",
            body=json.dumps(self.build_payload(cursor=None)),
            headers=self.api_headers,
            cookies=self.api_cookies,
            callback=self.parse_api_list
        )

    def parse_api_list(self, response):
        try:
            data = json.loads(response.body)
            
            if "errors" in data:
                self.logger.error(f"API Error: {data['errors']}")
                return

            messages = data.get("data", {}).get("messages", {})
            edges = messages.get("edges", [])
            
            self.logger.info(f"API returned {len(edges)} items.")
            
            for edge in edges:
                node = edge.get("node", {})
                # Try to find URL
                url = node.get("view_href")
                if not url:
                    # Construct URL from ID
                    msg_id = node.get("id", "").replace("message:", "")
                    if msg_id:
                        url = f"https://techcommunity.microsoft.com/t5/microsoft-365-copilot/discussion/m-p/{msg_id}"
                
                if url:
                    if url in self.previous_links:
                        continue
                        
                    self.seen_links.add(url)
                    
                    yield scrapy.Request(
                        url, 
                        self.parse_discussion,
                        meta={
                            "playwright": True,
                            "playwright_page_event_handlers": {
                                "response": handle_graphql_response,
                            },
                            "playwright_page_methods": [
                                PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight)"),
                                PageMethod("wait_for_timeout", 5000),
                            ],
                        }
                    )

            # Pagination
            page_info = messages.get("pageInfo", {})
            if page_info.get("hasNextPage"):
                end_cursor = page_info.get("endCursor")
                if end_cursor:
                    self.logger.info(f"Fetching next page with cursor: {end_cursor}")
                    yield scrapy.Request(
                        url="https://techcommunity.microsoft.com/t5/s/api/2.1/graphql?opname=MessageViewsForWidget",
                        method="POST",
                        body=json.dumps(self.build_payload(cursor=end_cursor)),
                        headers=self.api_headers,
                        cookies=self.api_cookies,
                        callback=self.parse_api_list
                    )
            else:
                self.logger.info("No more pages in API.")

        except Exception as e:
            self.logger.error(f"Error parsing API response: {e}")


    async def parse_discussion(self, response, page: TechcommunityMicrosoftComDiscussionItemPage):
        yield await page.to_item()
