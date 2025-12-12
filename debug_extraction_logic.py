import requests
import json
import re
import html
from datetime import datetime

def parse_single_reply_node(node, apollo_state):
    reply = {}
    
    # Author
    author_node = node.get("author", {})
    if "__ref" in author_node:
        ref_key = author_node["__ref"]
        author_node = apollo_state.get(ref_key, {})
        reply['author_resolved'] = True
    
    reply['author'] = author_node.get("login")
    
    # Content
    body = node.get("body", "")
    clean_body = re.sub(r'<[^>]+>', ' ', body)
    clean_body = html.unescape(re.sub(r'\s+', ' ', clean_body).strip())
    reply['content'] = clean_body
    
    # Publish Date
    post_time = node.get("postTime")
    reply['publish_date'] = post_time
    
    return reply

url = 'https://techcommunity.microsoft.com/discussions/microsoft365copilot/copilot-chat-vsus-microsoft-365-copilot-whats-the-difference/4382855'
r = requests.get(url)
match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)

if match:
    data = json.loads(match.group(1))
    apollo_state = data.get('props', {}).get('pageProps', {}).get('apolloState', {})
    
    all_reply_keys = [k for k in apollo_state.keys() if k.startswith('ForumReplyMessage:message:')]
    print(f"Found {len(all_reply_keys)} reply keys.")
    
    extracted = []
    for key in all_reply_keys:
        node = apollo_state[key]
        parsed = parse_single_reply_node(node, apollo_state)
        extracted.append(parsed)
        print(f"Key: {key} -> Author: {parsed.get('author')}, Date: {parsed.get('publish_date')}")


    # Test deduplication logic
    unique_replies = {}
    for r in extracted:
        # Simulating the dedupe key
        uid = f"{r.get('author')}_{r.get('publish_date')}_{r.get('content')[:20]}"
        unique_replies[uid] = r
    
    print(f"Unique replies after dedupe: {len(unique_replies)}")

else:
    print("__NEXT_DATA__ not found")
