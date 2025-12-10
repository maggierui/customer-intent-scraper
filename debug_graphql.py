import requests
import json

url = "https://techcommunity.microsoft.com/t5/s/api/2.1/graphql"
params = {
    "opname": "MessageReplies"
}

# The payload provided by the user
payload = {
    "operationName": "MessageReplies",
    "variables": {
        "after": None,
        "before": None,
        "constraints": {},
        "sorts": {"postTime": {"direction": "DESC"}},
        "repliesAfter": None,
        "repliesConstraints": {},
        "repliesSorts": {"postTime": {"direction": "DESC"}},
        "useAvatar": True,
        "useAuthorLogin": True,
        "useAuthorRank": True,
        "useBody": True,
        "useTextBody": False,
        "useKudosCount": True,
        "useTimeToRead": False,
        "useRevision": False,
        "useMedia": False,
        "useReadOnlyIcon": False,
        "useRepliesCount": True,
        "useSearchSnippet": False,
        "useAcceptedSolutionButton": True,
        "useSolvedBadge": False,
        "useAttachments": False,
        "attachmentsFirst": 5,
        "attachmentsAfter": None,
        "useTags": True,
        "tagsFirst": 0,
        "tagsAfter": None,
        "truncateBodyLength": 200,
        "useNodeAncestors": False,
        "useContentWorkflow": False,
        "useSpoilerFreeBody": False,
        "removeTocMarkup": False,
        "useUserHoverCard": False,
        "useNodeHoverCard": False,
        "useSeoAttributes": False,
        "useTextDescriptionForNode": True,
        "useModerationStatus": True,
        "usePreviewSubjectModal": False,
        "useUnreadCount": True,
        "useOccasionData": False,
        "useMessageStatus": True,
        "removeProcessingText": False,
        "useLatestRevision": False,
        "id": "message:4389520",
        "first": 10,
        "repliesFirst": 3,
        "repliesFirstDepthThree": 1
    },
    "extensions": {
        "persistedQuery": {
            "version": 1,
            "sha256Hash": "bdf33b497250518517b2f92d73b36bd00bab5b17a4ab95fff259bea3b9085bf5"
        }
    }
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "li-api-session-key": "true",
    # Extracted from the fixture HTML
    "x-lithium-ajax": "true",
    "x-requested-with": "XMLHttpRequest",
    # "Authorization": "Bearer b7AOHmZafAY7gqWPpXY6w3tUqxHiaNogIYSf1iUAFBI=",
    # "lia-common-csrf-token": "1464b073d1c5c678258ab88b5a692ba4e6768eda5206d06313926fc313e23f9682dbcac6248f624a662caafe3991751478d56ce33634fde489224a51572a9cc9"
}

print("Sending POST request...")
try:
    response = requests.post(url, params=params, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Success!")
        # Check if we got the expected data
        if "data" in data and "message" in data["data"]:
             replies_count = data["data"]["message"].get("repliesCount")
             print(f"Replies Count: {replies_count}")
             replies = data["data"]["message"].get("replies", {}).get("edges", [])
             print(f"Number of replies fetched: {len(replies)}")
        else:
             print("Response JSON structure unexpected:")
             print(json.dumps(data, indent=2)[:500])
    else:
        print("Error response:")
        print(response.text[:500])

except Exception as e:
    print(f"Exception: {e}")
