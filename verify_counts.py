import json

with open('debug_output.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    url = item.get('discussion_url', '')
    reply_count_meta = item.get('reply_count', 0)
    replies = item.get('replies') or []
    print(f"URL: {url}")
    print(f"Meta Count: {reply_count_meta}, Extracted Count: {len(replies)}")
    print("-" * 20)
