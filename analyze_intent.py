import json
import os
import sys

try:
    from openai import AzureOpenAI
except ImportError:
    print("Error: 'openai' library not found. Please install it using 'pip install openai'")
    sys.exit(1)

def load_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_intent(client, discussion, deployment_name):
    """
    Analyzes the customer intent of a discussion using an LLM.
    """
    title = discussion.get('title', '')
    content = discussion.get('content', '')
    
    system_prompt = "You are an expert customer support analyst. Your goal is to categorize the intent of technical forum discussions."
    user_prompt = f"""
    Analyze the following customer discussion.
    
    Title: {title}
    Content: {content}
    
    Provide the output in JSON format with the following keys:
    - "intent_category": (e.g., "Troubleshooting", "Feature Request", "How-to", "Feedback", "General Discussion")
    - "summary": A one-sentence summary of the issue.
    - "sentiment": (e.g., "Positive", "Neutral", "Negative", "Frustrated")
    - "urgency": (e.g., "Low", "Medium", "High")
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
        print(f"Error analyzing item '{title}': {e}")
        return None

def main():
    input_file = 'items_cleaned.json'
    output_file = 'intent_analysis.json'
    
    # Check for Azure OpenAI Environment Variables
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview") # Default version

    if not all([api_key, endpoint, deployment_name]):
        print("Error: Missing Azure OpenAI environment variables.")
        print("Please set the following variables:")
        print("- AZURE_OPENAI_API_KEY")
        print("- AZURE_OPENAI_ENDPOINT")
        print("- AZURE_OPENAI_DEPLOYMENT_NAME")
        print("- AZURE_OPENAI_API_VERSION (Optional, defaults to 2024-02-15-preview)")
        return

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Please run the scraper first.")
        return

    data = load_data(input_file)
    print(f"Loaded {len(data)} items. Starting analysis with Azure OpenAI...")

    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=endpoint
    )
    
    results = []
    for i, item in enumerate(data):
        print(f"Analyzing item {i+1}/{len(data)}: {item.get('title', 'No Title')[:50]}...")
        analysis = analyze_intent(client, item, deployment_name)
        if analysis:
            item['analysis'] = analysis
            results.append(item)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Analysis complete. Results saved to {output_file}")

if __name__ == "__main__":
    main()
