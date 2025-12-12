import requests
import re
import json

url = "https://techcommunity.microsoft.com/t5/copilot-for-small-and-medium-business/bd-p/CopilotforSmallandMediumBusiness"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers)
    content = response.text
    
    print(f"Status Code: {response.status_code}")
    
    # Look for boardId in the text
    matches = re.findall(r'"boardId"\s*:\s*"([^"]+)"', content)
    if matches:
        print("Found boardIds:", set(matches))
    else:
        print("No direct 'boardId' matches found.")
        
    # Look for board: pattern
    matches_board = re.findall(r'board:[a-zA-Z0-9]+', content)
    if matches_board:
        print("Found board: patterns:", set(matches_board))

except Exception as e:
    print(f"Error: {e}")
