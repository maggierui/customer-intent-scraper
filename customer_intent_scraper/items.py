# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ReplyItem(scrapy.Item):
    """A single reply in a discussion thread."""
    id = scrapy.Field()
    author = scrapy.Field()
    content = scrapy.Field()
    publish_date = scrapy.Field()
    thumbs_up_count = scrapy.Field()


class DiscussionItem(scrapy.Item):
    """Discussion metadata and content extracted from Microsoft 365 Copilot forums."""

    message_id = scrapy.Field()
    title = scrapy.Field()
    discussion_url = scrapy.Field()
    author = scrapy.Field()
    reply_count = scrapy.Field()
    thumbs_up_count = scrapy.Field()
    content = scrapy.Field()
    publish_date = scrapy.Field()
    replies = scrapy.Field()
