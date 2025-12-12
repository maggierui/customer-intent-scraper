import requests
import json
import re

url = 'https://techcommunity.microsoft.com/discussions/microsoft365copilot/copilot-chat-vsus-microsoft-365-copilot-whats-the-difference/4382855'
r = requests.get(url)
match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)

if match:
    data = json.loads(match.group(1))
    apollo = data.get('props', {}).get('pageProps', {}).get('apolloState', {})
    msg_key = 'ForumTopicMessage:message:4382855'
    
    if msg_key in apollo:
        replies = apollo[msg_key].get('replies', {})
        edges = replies.get('edges', [])
        print(f'Total edges in main message: {len(edges)}')
        
        # Check pagination info
        page_info = replies.get('pageInfo', {})
        print(f"Page Info: {page_info}")
        
    reply_keys = [k for k in apollo.keys() if 'ForumReplyMessage' in k]
    print(f'Total ForumReplyMessage keys in Apollo: {len(reply_keys)}')
else:
    print("__NEXT_DATA__ not found")
