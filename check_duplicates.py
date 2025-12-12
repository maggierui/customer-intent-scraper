import json

filepath = "all_discussions_backup.jsonl"
urls = set()
total_lines = 0
duplicates = 0

with open(filepath, 'r', encoding='utf-8') as f:
    for line in f:
        total_lines += 1
        try:
            item = json.loads(line)
            url = item.get('discussion_url')
            if url:
                if url in urls:
                    duplicates += 1
                else:
                    urls.add(url)
        except:
            pass

print(f"Total lines: {total_lines}")
print(f"Unique URLs: {len(urls)}")
print(f"Duplicates found: {duplicates}")
