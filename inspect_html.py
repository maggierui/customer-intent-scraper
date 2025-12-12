import re

with open("debug_spider_page.html", "r", encoding="utf-8") as f:
    content = f.read()

match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', content, re.DOTALL)
if match:
    data = match.group(1)
    print(f"Data length: {len(data)}")
    print("First 500 chars:")
    print(data[:500])
    print("-" * 20)
    print("Last 500 chars:")
    print(data[-500:])
else:
    print("__NEXT_DATA__ not found in file")
