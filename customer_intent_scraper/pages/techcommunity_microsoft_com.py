from datetime import datetime
from typing import Optional, List
import html
import re
import json
import logging
import attrs

from customer_intent_scraper.items import DiscussionItem, ReplyItem
from web_poet import Returns, WebPage, field, handle_urls, HttpResponse
from web_poet.serialization import register_serialization

logger = logging.getLogger(__name__)


@attrs.define
class TechcommunityReplies:
    data: dict


def _serialize_replies(o: TechcommunityReplies) -> dict:
    return {"json": json.dumps(o.data, sort_keys=True, indent=4).encode()}


def _deserialize_replies(cls, data: dict) -> TechcommunityReplies:
    return cls(data=json.loads(data["json"]))


register_serialization(_serialize_replies, _deserialize_replies)


@handle_urls("techcommunity.microsoft.com")
class TechcommunityMicrosoftComDiscussionItemPage(WebPage, Returns[DiscussionItem]):
    def __init__(self, response: HttpResponse, replies: Optional[TechcommunityReplies] = None):
        super().__init__(response)
        self.replies_input = replies

    @property
    def _next_data(self):
        if not hasattr(self, '__next_data'):
            data = self.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
            if data:
                try:
                    self.__next_data = json.loads(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse __NEXT_DATA__: {e}")
                    self.__next_data = {}
            else:
                self.__next_data = {}
        return self.__next_data

    @property
    def _main_message_data(self):
        if not hasattr(self, '__main_message_data'):
            self.__main_message_data = None
            apollo_state = self._next_data.get('props', {}).get('pageProps', {}).get('apolloState', {})
            
            # Try to find the message ID from the URL
            url_id = None
            match = re.search(r'/(\d+)$', str(self.response.url))
            if match:
                url_id = match.group(1)
            
            if url_id:
                key = f'ForumTopicMessage:message:{url_id}'
                if key in apollo_state:
                    self.__main_message_data = apollo_state[key]
            
            # Fallback: search for any ForumTopicMessage if URL ID extraction fails or key not found
            if not self.__main_message_data:
                for key, value in apollo_state.items():
                    if key.startswith('ForumTopicMessage:message:') and value.get('entityType') == 'FORUM_TOPIC':
                         # We might want to ensure it's the main topic, usually depth 0
                         if value.get('depth') == 0:
                             self.__main_message_data = value
                             break
        return self.__main_message_data

    @field
    def author(self) -> Optional[str]:
        # Detail page
        name = self.css('article[data-testid="StandardMessageView"] a[data-testid="userLink"]::text').get()
        if name:
            return name.strip()

        # Prefer the author link inside the first message item of the PanelItemList widget
        scoped_selector = (
            'article[data-testid="PanelItemList.MessageListForNodeByRecentActivityWidget"] '
            'section[role="tabpanel"] ul li:first-child a[data-testid="userLink"]::text'
        )
        name = self.css(scoped_selector).get()
        if not name:
            # Looser fallback: first userLink within the article container
            fallback_selector = (
                'article[data-testid="PanelItemList.MessageListForNodeByRecentActivityWidget"] '
                'a[data-testid="userLink"]::text'
            )
            name = self.css(fallback_selector).get()
        if not name:
            return None
        name = name.strip()
        return name or None

    @field
    def content(self) -> Optional[str]:
        # Detail page
        articles = self.css('article[data-testid="StandardMessageView"]')
        if articles:
            # Use the first one (main post)
            node = articles[0].css('div[class*="message-body"]')
            if node:
                texts = node.css("::text").getall()
                parts = [t.strip() for t in texts if t and t.strip()]
                combined = " ".join(parts)
                return html.unescape(re.sub(r"\s+", " ", combined).strip())

        # Scope to the first message item (the main post)
        scoped_selector = (
            'article[data-testid="PanelItemList.MessageListForNodeByRecentActivityWidget"] '
            'section[role="tabpanel"] ul li:first-child '
            'a[data-testid="MessageLink"] span[class*="message-body"]::text'
        )
        texts = self.css(scoped_selector).getall()
        
        if not texts:
             # Fallback: try without the span, just the anchor text in the first item
            fallback_selector = (
                'article[data-testid="PanelItemList.MessageListForNodeByRecentActivityWidget"] '
                'section[role="tabpanel"] ul li:first-child '
                'a[data-testid="MessageLink"]::text'
            )
            texts = self.css(fallback_selector).getall()

        # Clean and join pieces
        parts = [t.strip() for t in texts if t and t.strip()]
        if not parts:
            return None

        combined = " ".join(parts)
        collapsed = re.sub(r"\s+", " ", combined).strip()
        return html.unescape(collapsed)

    @field
    def discussion_url(self) -> Optional[str]:
        current_url = str(self.response.url)
        # If current URL already looks like a discussion permalink, use it.
        # Matches /discussions/category/slug/id or /discussions/category/id
        if re.search(r"/discussions/[^/]+/(?:[^/]+/)?\d+/?$", current_url):
            return current_url

        # Scope to the first message item (the main post) and get the MessageLink href
        scoped_selector = (
            'article[data-testid="PanelItemList.MessageListForNodeByRecentActivityWidget"] '
            'section[role="tabpanel"] ul li:first-child '
            'h4[data-testid="MessageSubject"] a[data-testid="MessageLink"]::attr(href)'
        )
        href = self.css(scoped_selector).get()
        
        if href:
            href = html.unescape(href.strip())
            return self.urljoin(href)

        # Fallback: try the first MessageLink in the list if the specific structure above fails
        fallback_selector = (
            'article[data-testid="PanelItemList.MessageListForNodeByRecentActivityWidget"] '
            'section[role="tabpanel"] ul li:first-child '
            'a[data-testid="MessageLink"]::attr(href)'
        )
        href = self.css(fallback_selector).get()
        if href:
             href = html.unescape(href.strip())
             return self.urljoin(href)

        return None

    @field
    def publish_date(self) -> Optional[str]:
        # Try to get the machine-friendly title attribute for the message time
        selectors = [
            # Detail page
            'article[data-testid="StandardMessageView"] [data-testid="messageTime"] span::attr(title)',

            # Restrict to the main panel widget to avoid picking other timestamps on the page
            'article[data-testid="PanelItemList.MessageListForNodeByRecentActivityWidget"] '
            '[data-testid="messageTime"] span::attr(title)',

            # Fallback: any messageTime span title attribute
            '[data-testid="messageTime"] span::attr(title)',

            # Some pages may put the title on the messageTime element itself
            '[data-testid="messageTime"]::attr(title)',

            # As last resort, use visible text inside the span (may lack time)
            '[data-testid="messageTime"] span::text',
            '[data-testid="messageTime"]::text',
        ]

        raw = None
        for sel in selectors:
            value = self.css(sel).get()
            if value:
                raw = value.strip()
                break

        if not raw:
            return None

        # Normalize common connector words
        normalized = raw.replace(" at ", " ").strip()

        formats = [
            "%B %d, %Y %I:%M %p",  # December 9, 2025 10:02 PM
            "%b %d, %Y %I:%M %p",  # Dec 9, 2025 10:02 PM
            "%B %d, %Y %H:%M",     # 24h if present
            "%b %d, %Y %H:%M",
            "%B %d, %Y",           # date only
            "%b %d, %Y",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(normalized, fmt)
                # If format did not include time, ensure time is midnight
                if fmt in ("%B %d, %Y", "%b %d, %Y"):
                    dt = datetime(dt.year, dt.month, dt.day, 0, 0, 0)
                return dt.strftime("%Y-%m-%dT%H:%M:%S")
            except ValueError:
                continue

        return None

    @field
    def reply_count(self) -> Optional[int]:
        if self._main_message_data:
            return self._main_message_data.get("repliesCount")
        
        texts = self.css('[data-testid="messageRepliesCount"]::text').getall()
        if not texts:
            texts = self.css('[data-testid*="messageRepliesCount"]::text').getall()
        cleaned = " ".join(part.strip() for part in texts if part and part.strip())
        if not cleaned:
            return None
        match = re.search(r"(\d+)", cleaned)
        if not match:
            return None
        try:
            return int(match.group(1))
        except ValueError:
            return None

    @field
    def thumbs_up_count(self) -> Optional[int]:
        if self._main_message_data:
            # Try kudosSumWeight first, then kudosCount
            val = self._main_message_data.get("kudosSumWeight")
            if val is None:
                val = self._main_message_data.get("kudosCount")
            if val is not None:
                return int(val)

        selector = self.css('[data-testid="kudosCount"]')
        if not selector:
            return None

        text = selector.xpath("string(.)").get()
        if not text:
            return None

        text = text.strip()
        # collapse whitespace
        text = re.sub(r"\s+", "", text)

        # Try match compact forms like 6.8K or 1.2M or plain numbers with separators
        m = re.match(r"^([0-9.,]+)([kKmM])?$", text)
        if m:
            number_text = m.group(1).replace(",", "")
            suffix = m.group(2)
            try:
                value = float(number_text)
            except ValueError:
                return None

            if suffix:
                if suffix.upper() == "K":
                    value = int(value * 1_000)
                elif suffix.upper() == "M":
                    value = int(value * 1_000_000)
                else:
                    value = int(value)
            else:
                # plain number, convert to int
                value = int(value)
            return value

        # Fallback: extract first contiguous number sequence
        fallback = re.search(r"([0-9][0-9,\.]*)", text)
        if not fallback:
            return None
        num_text = fallback.group(1).replace(",", "")
        try:
            return int(float(num_text))
        except ValueError:
            return None

    @field
    def title(self) -> Optional[str]:
        # Detail page
        title = self.css('article[data-testid="StandardMessageView"] h1[data-testid="MessageSubject"]::text').get()
        if title:
            return title.strip()

        # Prefer the subject link text inside the message list panel to avoid matching unrelated links.
        selectors = [
            # Most specific: subject anchor inside the panel list body
            'section[role="tabpanel"] h4[data-testid="MessageSubject"] a[data-testid="MessageLink"]::text',
            # Slightly broader: any message link inside the panel list body
            'section[role="tabpanel"] li a[data-testid="MessageLink"]::text',
            # Fallback to aria-label on the link (visible label), scoped to message links
            'section[role="tabpanel"] a[data-testid="MessageLink"]::attr(aria-label)',
            # Last resort: h4 title attribute
            'section[role="tabpanel"] h4[data-testid="MessageSubject"]::attr(title)',
            # Very broad fallback (less preferred)
            'a[data-testid="MessageLink"]::text',
        ]

        for sel in selectors:
            value = self.css(sel).get()
            if value:
                value = value.strip()
                if value:
                    return value

        return None

    @field
    def replies(self) -> List[ReplyItem]:
        replies = []

        # 1. Try to use JSON input if available
        if self.replies_input and self.replies_input.data:
            data = self.replies_input.data
            # Navigate to data.message.replies.edges
            message = data.get("data", {}).get("message", {})
            edges = message.get("replies", {}).get("edges", [])
            
            for edge in edges:
                node = edge.get("node", {})
                if not node:
                    continue
                    
                reply = ReplyItem()
                
                # Author
                author_node = node.get("author", {})
                reply['author'] = author_node.get("login")
                
                # Content
                body = node.get("body", "")
                # Remove HTML tags for content
                clean_body = re.sub(r'<[^>]+>', ' ', body)
                clean_body = html.unescape(re.sub(r'\s+', ' ', clean_body).strip())
                reply['content'] = clean_body
                
                # Publish Date
                post_time = node.get("postTime")
                if post_time:
                    # Format: 2025-12-09T14:02:22.388-08:00
                    # We need to parse this.
                    try:
                        # Remove milliseconds and timezone for simple parsing or use dateutil
                        # Using the existing _parse_date might not work directly as format differs
                        # Let's try to parse ISO format
                        dt = datetime.fromisoformat(post_time)
                        reply['publish_date'] = dt.isoformat()
                    except Exception:
                        reply['publish_date'] = post_time
                else:
                    reply['publish_date'] = None
                
                # Thumbs up
                reply['thumbs_up_count'] = node.get("kudosSumWeight", 0)
                
                replies.append(reply)
            
            return replies

        # Detail page: check for multiple StandardMessageView articles
        articles = self.css('article[data-testid="StandardMessageView"]')
        if articles and len(articles) > 1:
            # Skip the first one (main post)
            for item in articles[1:]:
                reply = ReplyItem()
                
                # Author
                author = item.css('a[data-testid="userLink"]::text').get()
                reply['author'] = author.strip() if author else None
                
                # Content
                node = item.css('div[class*="message-body"]')
                if node:
                    texts = node.css("::text").getall()
                    parts = [t.strip() for t in texts if t and t.strip()]
                    combined = " ".join(parts)
                    reply['content'] = html.unescape(re.sub(r"\s+", " ", combined).strip())
                else:
                    reply['content'] = None
                
                # Publish Date
                date_title = item.css('[data-testid="messageTime"] span::attr(title)').get()
                if not date_title:
                    date_title = item.css('[data-testid="messageTime"]::attr(title)').get()
                
                if date_title:
                    reply['publish_date'] = self._parse_date(date_title)
                else:
                    reply['publish_date'] = None
                
                # Thumbs up
                kudos_text = item.xpath('string(.//*[@data-testid="kudosCount"])').get()
                if kudos_text:
                    reply['thumbs_up_count'] = self._parse_kudos(kudos_text)
                else:
                    reply['thumbs_up_count'] = 0
                
                replies.append(reply)
            
            return replies

        # Select all list items except the first one (which is the main post)
        reply_items = self.css(
            'article[data-testid="PanelItemList.MessageListForNodeByRecentActivityWidget"] '
            'section[role="tabpanel"] ul li:not(:first-child)'
        )

        for item in reply_items:
            reply = ReplyItem()

            # Author
            author = item.css('a[data-testid="userLink"]::text').get()
            reply['author'] = author.strip() if author else None

            # Content
            texts = item.css('a[data-testid="MessageLink"] span[class*="message-body"]::text').getall()
            if not texts:
                texts = item.css('a[data-testid="MessageLink"]::text').getall()

            parts = [t.strip() for t in texts if t and t.strip()]
            if parts:
                combined = " ".join(parts)
                reply['content'] = html.unescape(re.sub(r"\s+", " ", combined).strip())
            else:
                reply['content'] = None

            # Thumbs up
            kudos_text = item.xpath('string(.//*[@data-testid="kudosCount"])').get()
            if kudos_text:
                reply['thumbs_up_count'] = self._parse_kudos(kudos_text)
            else:
                reply['thumbs_up_count'] = 0

            # Publish Date
            date_title = item.css('[data-testid="messageTime"] span::attr(title)').get()
            if not date_title:
                date_title = item.css('[data-testid="messageTime"]::attr(title)').get()

            if date_title:
                reply['publish_date'] = self._parse_date(date_title)
            else:
                reply['publish_date'] = None

            replies.append(reply)

        return replies

    def _parse_kudos(self, text: str) -> Optional[int]:
        text = text.strip()
        text = re.sub(r"\s+", "", text)
        m = re.match(r"^([0-9.,]+)([kKmM])?$", text)
        if m:
            number_text = m.group(1).replace(",", "")
            suffix = m.group(2)
            try:
                value = float(number_text)
            except ValueError:
                return None
            if suffix:
                if suffix.upper() == "K":
                    value = int(value * 1_000)
                elif suffix.upper() == "M":
                    value = int(value * 1_000_000)
                else:
                    value = int(value)
            else:
                value = int(value)
            return value

        fallback = re.search(r"([0-9][0-9,\.]*)", text)
        if not fallback:
            return None
        num_text = fallback.group(1).replace(",", "")
        try:
            return int(float(num_text))
        except ValueError:
            return None

    def _parse_date(self, raw: str) -> Optional[str]:
        normalized = raw.replace(" at ", " ").strip()
        formats = [
            "%B %d, %Y %I:%M %p",
            "%b %d, %Y %I:%M %p",
            "%B %d, %Y %H:%M",
            "%b %d, %Y %H:%M",
            "%B %d, %Y",
            "%b %d, %Y",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(normalized, fmt)
                if fmt in ("%B %d, %Y", "%b %d, %Y"):
                    dt = datetime(dt.year, dt.month, dt.day, 0, 0, 0)
                return dt.strftime("%Y-%m-%dT%H:%M:%S")
            except ValueError:
                continue
        return None
