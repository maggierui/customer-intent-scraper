import scrapy
from customer_intent_scraper.pages.techcommunity_microsoft_com import TechcommunityMicrosoftComDiscussionItemPage

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
                yield response.follow(link, self.parse_discussion)

        # Pagination: Look for a "Next" button or link. 
        # Common pattern in Lithium/Khoros communities (which this looks like) is a link with rel="next"
        next_page = response.css('a[rel="next"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)

    async def parse_discussion(self, response, page: TechcommunityMicrosoftComDiscussionItemPage):
        yield await page.to_item()
