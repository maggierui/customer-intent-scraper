import json
import random

try:
    with open('discussions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Filter for discussions that have content (some might be empty)
    valid_discussions = [d for d in data if d.get('content') and len(d.get('content')) > 50]
    
    # Sample 20 discussions
    sample = random.sample(valid_discussions, min(20, len(valid_discussions)))
    
    print(f"--- Analysis Sample ({len(sample)} items) ---")
    for i, d in enumerate(sample):
        print(f"\n[{i+1}] Title: {d.get('title')}")
        print(f"    Content Preview: {d.get('content')[:200]}...")
        
except Exception as e:
    print(f"Error: {e}")
