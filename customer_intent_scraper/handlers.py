import logging
from customer_intent_scraper.stores import replies_cache

logger = logging.getLogger(__name__)

async def handle_graphql_response(response):
    try:
        # Check if this is the GraphQL request we are interested in
        url = response.url
        if "graphql" in url:
            # Check request body for operationName
            try:
                request = response.request
                post_data = request.post_data
                if post_data and "MessageReplies" in str(post_data):
                    json_data = await response.json()
                    # We need to associate this with the main page URL.
                    page = response.frame.page
                    if page:
                        main_url = page.url
                        replies_cache[main_url] = json_data
                        logger.info(f"Captured GraphQL replies for {main_url}")
            except Exception as e:
                # It might not be a POST request or have post_data
                pass
    except Exception as e:
        logger.error(f"Error in handle_graphql_response: {e}")
