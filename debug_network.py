from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("Navigating to page...")
        page.goto("https://techcommunity.microsoft.com/category/microsoft365copilot/discussions/microsoft365copilot")
        
        print("Waiting for page load...")
        page.wait_for_timeout(5000)

        print("Setting up request listener...")
        def log_response(response):
            if "MessageViewsForWidget" in response.url:
                print(f"API RESPONSE: {response.status} {response.url}")
                try:
                    print(f"RESPONSE BODY: {response.body()[:500]}") # Print first 500 chars
                except:
                    pass

        page.on("response", log_response)
        
        try:
            print("Looking for Show More button...")
            show_more = page.locator('button[data-testid="PagerLoadMore.Button"]').filter(has_text="Show More").last
            if show_more.is_visible():
                print("Clicking Show More...")
                show_more.click()
                print("Waiting for network activity...")
                page.wait_for_timeout(5000)
            else:
                print("Show More button not found or not visible.")
        except Exception as e:
            print(f"Error interacting with button: {e}")
            
        browser.close()
        print("Done.")

if __name__ == "__main__":
    run()
