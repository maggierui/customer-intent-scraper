import sys
import os

# Add current directory to path so we can import the project modules
sys.path.append(os.getcwd())

import requests
from web_poet import HttpResponse
from customer_intent_scraper.pages.techcommunity_microsoft_com import TechcommunityMicrosoftComDiscussionItemPage

def test_single_page():
    # This URL is the one the user is looking at (37 replies)
    url = "https://techcommunity.microsoft.com/discussions/microsoft365copilot/copilot-chat-vsus-microsoft-365-copilot-whats-the-difference/4382855"
    
    print(f"Fetching {url}...")
    # Mimic the headers a browser might send, just in case
    # headers = {
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    # }
    # resp = requests.get(url, headers=headers)
    resp = requests.get(url)
    print(f"Status: {resp.status_code}")

    if resp.status_code != 200:
        print("Failed to fetch page.")
        return

    # Create a web_poet HttpResponse (this is what the Page Object expects)
    poet_response = HttpResponse(url=url, body=resp.content, encoding="utf-8")

    # Instantiate the page object
    page = TechcommunityMicrosoftComDiscussionItemPage(response=poet_response)

    # Test extraction
    print("-" * 30)
    print(f"Title: {page.title}")
    print(f"Reply Count: {page.reply_count}")
    
    replies = page.replies
    print(f"Replies Extracted: {len(replies)}")
    
    if replies:
        print("-" * 30)
        print("First Reply Details:")
        print(f"Author: {replies[0].get('author')}")
        print(f"Content Preview: {replies[0].get('content')[:100]}...")
        print(f"Date: {replies[0].get('publish_date')}")
    else:
        print("No replies found (unexpected for this URL).")

if __name__ == "__main__":
    test_single_page()
