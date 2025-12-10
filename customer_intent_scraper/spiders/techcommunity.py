import scrapy
from scrapy_playwright.page import PageMethod
from customer_intent_scraper.pages.techcommunity_microsoft_com import TechcommunityMicrosoftComDiscussionItemPage
from customer_intent_scraper.handlers import handle_graphql_response

class TechcommunitySpider(scrapy.Spider):
    name = "techcommunity"
    allowed_domains = ["techcommunity.microsoft.com"]
    start_urls = ["https://techcommunity.microsoft.com/category/microsoft365copilot/discussions/microsoft365copilot"]
    seen_links = set()

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                },
                callback=self.parse
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        
        try:
            while True:
                # Extract links from the current state of the page
                links = await page.locator('h4[data-testid="MessageSubject"] a[data-testid="MessageLink"]').evaluate_all("els => els.map(el => el.href)")
                
                new_links_count = 0
                for link in links:
                    if link and link not in self.seen_links:
                        self.seen_links.add(link)
                        new_links_count += 1
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
                
                self.logger.info(f"Found {new_links_count} new links. Total seen: {len(self.seen_links)}")

                # Check for "Show More" button
                show_more = page.locator('button[data-testid="PagerLoadMore.Button"]').first
                if await show_more.is_visible():
                    self.logger.info("Clicking 'Show More'...")
                    await show_more.click()
                    # Wait for the button to be enabled again or for new content
                    # A simple timeout is a safe bet for now, or we could wait for the number of items to increase
                    await page.wait_for_timeout(3000) 
                else:
                    self.logger.info("No more 'Show More' button found or it is not visible.")
                    break
        finally:
            await page.close()

    async def parse_discussion(self, response, page: TechcommunityMicrosoftComDiscussionItemPage):
        yield await page.to_item()
