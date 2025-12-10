import attrs
from scrapy import Request
from scrapy.http import Response
from scrapy_poet import PageObjectInputProvider
from web_poet import Injectable

from customer_intent_scraper.pages.techcommunity_microsoft_com import TechcommunityReplies
from customer_intent_scraper.stores import replies_cache

class TechcommunityRepliesProvider(PageObjectInputProvider):
    provided_classes = {TechcommunityReplies}

    def __call__(self, to_provide, response: Response):
        # Check if we have cached data for this URL
        url = response.url
        data = replies_cache.get(url)
        
        if data:
            return [TechcommunityReplies(data=data)]
        
        # If not found, return empty or None?
        # The Page Object expects Optional[TechcommunityReplies]
        # But the provider must return instances for the requested classes.
        # If we return None, it might fail if the type hint is strict.
        # But TechcommunityReplies is a data class.
        return [TechcommunityReplies(data={})]
