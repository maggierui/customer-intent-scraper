import requests
import json
import re

url = 'https://techcommunity.microsoft.com/discussions/microsoft365copilot/copilot-for-m365-shortcut/4169059'
try:
    r = requests.get(url)
    print(f"Response length: {len(r.text)}")
    print(f"Response start: {r.text[:500]}")
    if "__NEXT_DATA__" in r.text:
        print("__NEXT_DATA__ string found in response")
        idx = r.text.find("__NEXT_DATA__")
        print(f"Context: {r.text[idx-50:idx+100]}")
    else:
        print("__NEXT_DATA__ string NOT found in response")

    # Robust regex to handle attributes like crossorigin="anonymous"
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
    if match:
        data = json.loads(match.group(1))
        apollo = data.get('props', {}).get('pageProps', {}).get('apolloState', {})
        print(f'Apollo keys count: {len(apollo)}')
        keys = list(apollo.keys())
        print(f'Sample keys: {keys[:10]}')
        
        msg_key = 'ForumTopicMessage:message:4169059'
        print(f'Key {msg_key} exists: {msg_key in apollo}')
        
        forum_keys = [k for k in keys if 'ForumTopicMessage' in k]
        print(f'ForumTopicMessage keys: {forum_keys[:5]}')
        
        # Check if we can find replies in apolloState
        if msg_key in apollo:
            msg_data = apollo[msg_key]
            print(f"Message Data Keys: {list(msg_data.keys())}")
            if 'replies' in msg_data:
                print(f"Replies field: {msg_data['replies']}")
    else:
        print('__NEXT_DATA__ not found')
except Exception as e:
    print(f"Error: {e}")
