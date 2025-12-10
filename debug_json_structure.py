import json
from parsel import Selector

file_path = r"c:\GitHub\scraping-copilot\fixtures\customer_intent_scraper.pages.techcommunity_microsoft_com.TechcommunityMicrosoftComDiscussionItemPage\test-1\inputs\HttpResponse-body.html"

with open(file_path, "r", encoding="utf-8") as f:
    html_content = f.read()

sel = Selector(text=html_content)
script_content = sel.xpath('//script[@id="__NEXT_DATA__"]/text()').get()

if script_content:
    data = json.loads(script_content)
    apollo_state = data.get("props", {}).get("pageProps", {}).get("apolloState", {})
    
    # Find the main message
    main_message = None
    for key, value in apollo_state.items():
        if key.startswith("ForumTopicMessage:message:") and value.get("entityType") == "FORUM_TOPIC" and value.get("depth") == 0:
            main_message = value
            print(f"Found Main Message: {key}")
            break
            
    if main_message:
        # Check for replies
        print("Main Message Keys:", list(main_message.keys()))
        
        # Look for replies connection or list
        if 'replies' in main_message:
            print("Replies field found:", main_message['replies'])
        else:
            print("No direct 'replies' field. Searching for related keys...")
            for k in main_message:
                if 'replies' in k.lower():
                    print(f"Potential match: {k} -> {main_message[k]}")

    print("PageProps Keys:", list(data.get("props", {}).get("pageProps", {}).keys()))
    
    print("\n--- Apollo State Keys Sample ---")
    keys = list(apollo_state.keys())
    print(keys[:20])
    
    # 3. Inspect ROOT_QUERY for lists, filtering out noise
    print("\n--- ROOT_QUERY Lists (Filtered) ---")
    root_query = apollo_state.get("ROOT_QUERY", {})
    for key, value in root_query.items():
        if key.startswith("cachedText") or key.startswith("allowedLanguages"):
            continue
            
        print(f"Query Key: {key}")
        if isinstance(value, list):
             print(f"  -> List of {len(value)} items")
             if len(value) > 0 and isinstance(value[0], dict) and "__ref" in value[0]:
                 print(f"    First ref: {value[0]['__ref']}")
        elif isinstance(value, dict):
             if "__ref" in value:
                 print(f"  -> Ref: {value['__ref']}")
             else:
                 print(f"  -> Dict keys: {list(value.keys())}")
                 
    # 5. Find ALL ForumTopicMessage objects
    print("\n--- All ForumTopicMessage Objects ---")
    message_keys = [k for k in apollo_state.keys() if "ForumTopicMessage" in k]
    print(f"Found {len(message_keys)} message objects")
    for k in message_keys:
        print(k)
        
    # 6. If we have multiple messages, find who references them
    if len(message_keys) > 1:
        print("\n--- Finding References to Messages ---")
        other_messages = [k for k in message_keys if "4389520" not in k] # Exclude main message if possible, though ID might be different
        
        # If all messages have the same ID (unlikely for replies), then we are confused.
        # But usually replies have their own IDs.
        
        for msg_key in message_keys:
            print(f"\nSearching for references to {msg_key}...")
            ref_str = f'{{"__ref":"{msg_key}"}}' # JSON string representation of ref
            
            # Naive search in all values
            for key, value in apollo_state.items():
                # Check if value is a dict with __ref
                if isinstance(value, dict):
                    for k, v in value.items():
                        if isinstance(v, dict) and v.get("__ref") == msg_key:
                             print(f"  Referenced by {key}.{k}")
                        elif isinstance(v, list):
                             for i, item in enumerate(v):
                                 if isinstance(item, dict) and item.get("__ref") == msg_key:
                                     print(f"  Referenced by {key}.{k}[{i}]")
                                     
                # Check ROOT_QUERY keys specifically
                if key == "ROOT_QUERY":
                    for k, v in value.items():
                        if isinstance(v, dict) and v.get("__ref") == msg_key:
                             print(f"  Referenced by ROOT_QUERY.{k}")
                        elif isinstance(v, list):
                             for i, item in enumerate(v):
                                 if isinstance(item, dict) and item.get("__ref") == msg_key:
                                     print(f"  Referenced by ROOT_QUERY.{k}[{i}]")
            
    # Check for any list of messages in ROOT_QUERY
    print("\n--- ROOT_QUERY Lists ---")
    root_query = apollo_state.get("ROOT_QUERY", {})
    for key, value in root_query.items():
        if isinstance(value, list) and len(value) > 0:
             print(f"Query: {key} -> List of {len(value)} items")
             if isinstance(value[0], dict) and '__ref' in value[0]:
                 print(f"  First ref: {value[0]['__ref']}")




else:
    print("Script tag not found")
