import json
import csv
import os

def json_to_csv(input_file, output_file):
    print(f"Reading {input_file}...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {input_file} not found.")
        return

    # Define headers based on user request + available fields
    # User requested: message_id, author, publish_date, content, ...
    headers = [
        'message_id', 
        'author', 
        'publish_date', 
        'content', 
        'thumbs_up_count', 
        'type',             # Discussion or Reply
        'title',            # Discussion title (included for replies for context)
        'discussion_url',   # Discussion URL (included for replies for context)
        'reply_count',      # Only for discussions
        'parent_id'         # ID of the discussion for replies
    ]

    print(f"Writing to {output_file}...")
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        count = 0
        for discussion in data:
            # 1. Write the main discussion row
            row = {
                'message_id': discussion.get('message_id'),
                'author': discussion.get('author'),
                'publish_date': discussion.get('publish_date'),
                'content': discussion.get('content'),
                'thumbs_up_count': discussion.get('thumbs_up_count'),
                'type': 'Discussion',
                'title': discussion.get('title'),
                'discussion_url': discussion.get('discussion_url'),
                'reply_count': discussion.get('reply_count'),
                'parent_id': None
            }
            writer.writerow(row)
            count += 1

            # 2. Write rows for each reply
            replies = discussion.get('replies')
            if replies:
                for reply in replies:
                    reply_row = {
                        'message_id': reply.get('id'), # Replies use 'id' in the JSON
                        'author': reply.get('author'),
                        'publish_date': reply.get('publish_date'),
                        'content': reply.get('content'),
                        'thumbs_up_count': reply.get('thumbs_up_count'),
                        'type': 'Reply',
                        'title': discussion.get('title'), # Inherit title for context
                        'discussion_url': discussion.get('discussion_url'), # Inherit URL
                        'reply_count': None,
                        'parent_id': discussion.get('message_id')
                    }
                    writer.writerow(reply_row)
                    count += 1
    
    print(f"Successfully converted {len(data)} discussions and their replies into {count} rows in {output_file}.")

if __name__ == "__main__":
    json_to_csv('discussions.json', 'discussions.csv')
