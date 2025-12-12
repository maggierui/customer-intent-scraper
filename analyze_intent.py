import json
import os
import sys
import argparse
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    from openai import AzureOpenAI
except ImportError:
    print("Error: 'openai' library not found. Please install it using 'pip install openai'")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs): return iterable

def load_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_intent(client, discussion, deployment_name):
    """
    Analyzes the customer intent and pain points of a discussion using an LLM.
    """
    title = discussion.get('title', '')
    content = discussion.get('content', '')
    
    # Skip empty content
    if not content or len(content) < 10:
        return None

    system_prompt = "You are an expert product analyst for Microsoft 365 Copilot. Your goal is to identify customer pain points and categorize feedback."
    user_prompt = f"""
    Analyze the following customer discussion thread.
    
    Title: {title}
    Content: {content}
    
    Provide the output in JSON format with the following keys:
    - "category": (e.g., "Bug/Error", "Feature Request", "How-to/Question", "Pricing/Licensing", "General Feedback")
    - "product_area": (e.g., "Excel", "Outlook", "Teams", "PowerPoint", "Admin Center", "Copilot Studio", "General")
    - "pain_points": A list of specific struggles or issues mentioned (max 3).
    - "sentiment": (e.g., "Positive", "Neutral", "Negative", "Frustrated")
    - "summary": A concise one-sentence summary of the core issue.
    """
    
    try:
        response = client.chat.completions.create(
            model=deployment_name, 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        # print(f"Error analyzing item '{title[:30]}...': {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Analyze discussion intents using Azure OpenAI.")
    parser.add_argument("--input", default="discussions.json", help="Input JSON file path")
    parser.add_argument("--output", default="discussions_analyzed.json", help="Output JSON file path")
    parser.add_argument("--limit", type=int, default=10, help="Number of items to analyze (default: 10). Set to 0 for all.")
    args = parser.parse_args()

    # Check for Azure OpenAI Environment Variables
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

    if not all([api_key, endpoint, deployment_name]):
        print("Error: Missing Azure OpenAI environment variables.")
        print("Please set: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME")
        return

    if not os.path.exists(args.input):
        print(f"Error: {args.input} not found.")
        return

    data = load_data(args.input)
    total_items = len(data)
    
    # Apply limit
    if args.limit > 0:
        data = data[:args.limit]
        print(f"Processing {len(data)} items (limited from {total_items})...")
    else:
        print(f"Processing all {total_items} items...")

    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=endpoint
    )
    
    results = []
    print("Starting analysis...")
    
    for item in tqdm(data, desc="Analyzing"):
        analysis = analyze_intent(client, item, deployment_name)
        if analysis:
            item['analysis'] = analysis
            results.append(item)
        # Small sleep to avoid aggressive rate limiting if needed, though usually handled by client retries
        # time.sleep(0.1) 

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nAnalysis complete. {len(results)} items saved to {args.output}")

if __name__ == "__main__":
    main()
