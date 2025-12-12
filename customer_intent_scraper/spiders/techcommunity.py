import scrapy
import json
import os
import asyncio
import sys
import re
import html
from datetime import datetime

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
                            # Disable Playwright for detail page to avoid HTML truncation issues
                            # "playwright": True,
                            # "playwright_page_event_handlers": {
                            #     "response": handle_graphql_response,
                            # },
                            # "playwright_page_methods": [
                            #     PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight)"),
                            #     PageMethod("wait_for_timeout", 5000),
                            # ],
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
        item = await page.to_item()
        
        # Check if we need to fetch more replies
        reply_count = item.get('reply_count') or 0
        extracted_replies = item.get('replies') or []
        extracted_count = len(extracted_replies)
        message_id = item.get('message_id')
        
        if reply_count > extracted_count and self.api_headers and message_id:
            self.logger.info(f"Fetching more replies for {message_id} ({extracted_count}/{reply_count})")
            
            yield scrapy.Request(
                url="https://techcommunity.microsoft.com/t5/s/api/2.1/graphql?opname=MessageReplies",
                method="POST",
                body=json.dumps(self.build_replies_payload(message_id, cursor=None)),
                headers=self.api_headers,
                cookies=self.api_cookies,
                callback=self.parse_replies_api,
                meta={
                    "item": item, 
                    "message_id": message_id,
                    "root_message_id": message_id,
                    "reply_queue": [],
                    "visited_ids": set()
                },
                dont_filter=True
            )
        else:
            yield item

    def build_replies_payload(self, message_id, cursor=None):
        return {
            "operationName": "MessageReplies",
            "variables": {
                "after": None,
                "before": None,
                "constraints": {},
                "sorts": {"postTime": {"direction": "DESC"}},
                "repliesAfter": cursor,
                "repliesConstraints": {},
                "repliesSorts": {"postTime": {"direction": "DESC"}},
                "useAvatar": True,
                "useAuthorLogin": True,
                "useAuthorRank": True,
                "useBody": True,
                "useTextBody": False,
                "useKudosCount": True,
                "useTimeToRead": False,
                "useRevision": False,
                "useMedia": False,
                "useReadOnlyIcon": False,
                "useRepliesCount": True,
                "useSearchSnippet": False,
                "useAcceptedSolutionButton": True,
                "useSolvedBadge": False,
                "useAttachments": False,
                "attachmentsFirst": 5,
                "attachmentsAfter": None,
                "useTags": True,
                "tagsFirst": 0,
                "tagsAfter": None,
                "truncateBodyLength": 200,
                "useNodeAncestors": False,
                "useContentWorkflow": False,
                "useSpoilerFreeBody": False,
                "removeTocMarkup": False,
                "useUserHoverCard": False,
                "useNodeHoverCard": False,
                "useSeoAttributes": False,
                "useTextDescriptionForNode": True,
                "useModerationStatus": True,
                "usePreviewSubjectModal": False,
                "useUnreadCount": True,
                "useOccasionData": False,
                "useMessageStatus": True,
                "removeProcessingText": False,
                "useLatestRevision": False,
                "id": message_id,
                "first": 50,
                "repliesFirst": 50,
                "repliesFirstDepthThree": 100
            },
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "bdf33b497250518517b2f92d73b36bd00bab5b17a4ab95fff259bea3b9085bf5"
                }
            }
        }

    def _parse_reply_node(self, node):
        reply = {
            "id": node.get("id"),
            "author": node.get("author", {}).get("login"),
            "content": node.get("body", ""),
            "publish_date": node.get("postTime"),
            "thumbs_up_count": node.get("kudosCount", 0)
        }

        # Normalize date
        post_time = reply["publish_date"]
        if post_time:
            try:
                dt = datetime.fromisoformat(post_time)
                dt = dt.replace(microsecond=0)
                reply['publish_date'] = dt.isoformat()
            except Exception:
                pass
        
        # Clean content
        if reply["content"]:
            clean_body = re.sub(r'<[^>]+>', ' ', reply["content"])
            reply["content"] = html.unescape(re.sub(r'\s+', ' ', clean_body).strip())
            
        return reply

    def _extract_replies_recursive(self, edges):
        replies = []
        missing_ids = []
        for edge in edges:
            node = edge.get("node", {})
            # Extract current reply
            reply = self._parse_reply_node(node)
            replies.append(reply)
            
            # Extract nested replies
            nested_replies_connection = node.get("replies", {})
            nested_edges = nested_replies_connection.get("edges", [])
            replies_count = node.get("repliesCount", 0)
            
            if replies_count > len(nested_edges):
                 missing_ids.append(node.get("id"))

            if nested_edges:
                nested_replies, nested_missing = self._extract_replies_recursive(nested_edges)
                replies.extend(nested_replies)
                missing_ids.extend(nested_missing)
        return replies, missing_ids

    def parse_replies_api(self, response):
        item = response.meta["item"]
        message_id = response.meta["message_id"]
        root_message_id = response.meta.get("root_message_id", message_id)
        reply_queue = response.meta.get("reply_queue", [])
        visited_ids = response.meta.get("visited_ids", set())
        
        # Ensure visited_ids is a set
        if isinstance(visited_ids, list):
            visited_ids = set(visited_ids)
            
        visited_ids.add(message_id)
        
        try:
            data = json.loads(response.body)
            if "errors" in data:
                self.logger.error(f"API Error fetching replies for {message_id}: {data['errors']}")
                # Continue processing queue
            else:
                message_data = data.get("data", {}).get("message", {})
                replies_connection = message_data.get("replies", {})
                edges = replies_connection.get("edges", [])
                
                self.logger.info(f"API returned {len(edges)} top-level replies for {message_id}")
                
                # Recursively extract all replies
                new_replies, missing_ids = self._extract_replies_recursive(edges)
                self.logger.info(f"Extracted {len(new_replies)} total replies from this batch for {message_id}. Found {len(missing_ids)} incomplete nodes.")
                
                # Merge with existing replies
                existing_replies = item.get('replies') or []
                
                # Create a set of IDs for existing replies
                seen_ids = set()
                for r in existing_replies:
                    rid = r.get('id')
                    if rid:
                        seen_ids.add(rid)
                    else:
                        author = r.get('author')
                        date = r.get('publish_date')
                        sig = f"{author}_{date}"
                        seen_ids.add(sig)
                
                for r in new_replies:
                    rid = r.get('id')
                    if rid:
                        if rid not in seen_ids:
                            existing_replies.append(r)
                            seen_ids.add(rid)
                    else:
                        sig = f"{r.get('author')}_{r.get('publish_date')}"
                        if sig not in seen_ids:
                            existing_replies.append(r)
                            seen_ids.add(sig)
                
                item['replies'] = existing_replies
                
                # Add missing IDs to queue if not visited
                for mid in missing_ids:
                    if mid and mid not in visited_ids and mid not in reply_queue:
                        reply_queue.append(mid)
            
            # Process next item in queue
            if reply_queue:
                next_id = reply_queue.pop(0)
                self.logger.info(f"Fetching missing nested replies for {next_id}. Queue size: {len(reply_queue)}")
                yield scrapy.Request(
                    url="https://techcommunity.microsoft.com/t5/s/api/2.1/graphql?opname=MessageReplies",
                    method="POST",
                    body=json.dumps(self.build_replies_payload(next_id, cursor=None)),
                    headers=self.api_headers,
                    cookies=self.api_cookies,
                    callback=self.parse_replies_api,
                    meta={
                        "item": item, 
                        "message_id": next_id, 
                        "root_message_id": root_message_id,
                        "reply_queue": reply_queue,
                        "visited_ids": visited_ids
                    },
                    dont_filter=True
                )
            else:
                # Check for main pagination (only if we are processing the root message)
                if message_id == root_message_id and "data" in data and "errors" not in data:
                     message_data = data.get("data", {}).get("message", {})
                     replies_connection = message_data.get("replies", {})
                     page_info = replies_connection.get("pageInfo", {})
                     if page_info.get("hasNextPage"):
                        end_cursor = page_info.get("endCursor")
                        if end_cursor:
                            self.logger.info(f"Fetching next page for {message_id}")
                            yield scrapy.Request(
                                url="https://techcommunity.microsoft.com/t5/s/api/2.1/graphql?opname=MessageReplies",
                                method="POST",
                                body=json.dumps(self.build_replies_payload(message_id, cursor=end_cursor)),
                                headers=self.api_headers,
                                cookies=self.api_cookies,
                                callback=self.parse_replies_api,
                                meta={
                                    "item": item, 
                                    "message_id": message_id, 
                                    "root_message_id": root_message_id,
                                    "reply_queue": reply_queue,
                                    "visited_ids": visited_ids
                                },
                                dont_filter=True
                            )
                            return

                self.logger.info(f"Finished fetching replies for {root_message_id}. Total extracted: {len(item['replies'])}")
                yield item

        except Exception as e:
            self.logger.error(f"Error parsing replies API response: {e}")
            # Try to continue with queue if possible
            if reply_queue:
                 next_id = reply_queue.pop(0)
                 yield scrapy.Request(
                    url="https://techcommunity.microsoft.com/t5/s/api/2.1/graphql?opname=MessageReplies",
                    method="POST",
                    body=json.dumps(self.build_replies_payload(next_id, cursor=None)),
                    headers=self.api_headers,
                    cookies=self.api_cookies,
                    callback=self.parse_replies_api,
                    meta={
                        "item": item, 
                        "message_id": next_id, 
                        "root_message_id": root_message_id,
                        "reply_queue": reply_queue,
                        "visited_ids": visited_ids
                    },
                    dont_filter=True
                )
            else:
                yield item
