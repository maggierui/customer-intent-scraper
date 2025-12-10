import scrapy
from scrapy_playwright.page import PageMethod

class DebugPaginationSpider(scrapy.Spider):
    name = "debug_pagination"
    allowed_domains = ["techcommunity.microsoft.com"]
    start_urls = ["https://techcommunity.microsoft.com/category/microsoft365copilot/discussions/microsoft365copilot"]

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
        
        # Try to find the "Show More" button
        # We look for something containing "Show More"
        try:
            # Wait for the button to be visible
            button = page.locator("text=Show More")
            if await button.count() > 0:
                print("Found 'Show More' button!")
                # Get the outer HTML to see classes and attributes
                html = await button.evaluate("el => el.outerHTML")
                print(f"Button HTML: {html}")
                
                # Also check parent to see if it's wrapped in something
                parent_html = await button.evaluate("el => el.parentElement.outerHTML")
                print(f"Parent HTML: {parent_html}")
            else:
                print("'Show More' button not found with text locator.")
                
                # Dump the bottom of the page to see what's there
                content = await page.content()
                print("Page content length:", len(content))
                
        except Exception as e:
            print(f"Error finding button: {e}")

        await page.close()
