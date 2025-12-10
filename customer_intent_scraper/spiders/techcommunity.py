import scrapy
from scrapy_playwright.page import PageMethod
from customer_intent_scraper.pages.techcommunity_microsoft_com import TechcommunityMicrosoftComDiscussionItemPage
from customer_intent_scraper.handlers import handle_graphql_response

class TechcommunitySpider(scrapy.Spider):
    name = "techcommunity"
    allowed_domains = ["techcommunity.microsoft.com"]
    start_urls = ["https://techcommunity.microsoft.com/category/microsoft365copilot/discussions/microsoft365copilot"]

    def parse(self, response):
        # Extract discussion links using the specific class and data-testid from the provided HTML
        # The HTML shows: <h4 ... data-testid="MessageSubject"><a ... data-testid="MessageLink" href="...">
        links = response.css('h4[data-testid="MessageSubject"] a[data-testid="MessageLink"]::attr(href)').getall()
        
        for link in links:
            if link:
                # Use Playwright for discussion pages to capture GraphQL replies
                yield response.follow(
                    link, 
                    self.parse_discussion,
                    meta={
                        "playwright": True,
                        "playwright_page_event_handlers": {
                            "response": handle_graphql_response,
                        },
                        "playwright_page_methods": [
                            # Scroll to the bottom to trigger lazy loading of replies
                            PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight)"),
                            # Wait for network requests to complete (adjust time as needed)
                            PageMethod("wait_for_timeout", 5000),
                        ],
                    }
                )

        # Pagination: Look for a "Next" button or link. 
        # Common pattern in Lithium/Khoros communities (which this looks like) is a link with rel="next"
        next_page = response.css('a[rel="next"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)

    async def parse_discussion(self, response, page: TechcommunityMicrosoftComDiscussionItemPage):
        yield await page.to_item()
