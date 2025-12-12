import json
import re
import argparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from collections import Counter

def load_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def clean_text(text):
    if not text:
        return ""
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    # Remove special chars and numbers
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return text.lower()

def get_product_area(text):
    text = text.lower()
    products = {
        "excel": "Excel",
        "word": "Word",
        "powerpoint": "PowerPoint",
        "outlook": "Outlook",
        "teams": "Teams",
        "copilot studio": "Copilot Studio",
        "loop": "Loop",
        "onenote": "OneNote",
        "whiteboard": "Whiteboard",
        "admin": "Admin Center",
        "security": "Security",
        "compliance": "Compliance",
        "windows": "Windows",
        "power bi": "Power BI",
        "power automate": "Power Automate"
    }
    
    for key, value in products.items():
        if key in text:
            return value
    return "General"

def analyze_sentiment_keyword(text):
    # Very basic keyword-based sentiment since we don't have a model
    text = text.lower()
    neg_words = ["fail", "error", "bug", "broken", "issue", "problem", "slow", "crash", "stuck", "hate", "useless", "frustrat"]
    pos_words = ["great", "love", "amazing", "helpful", "thanks", "good", "excellent", "awesome"]
    
    neg_count = sum(1 for w in neg_words if w in text)
    pos_count = sum(1 for w in pos_words if w in text)
    
    if neg_count > pos_count:
        return "Negative"
    elif pos_count > neg_count:
        return "Positive"
    else:
        return "Neutral"

def main():
    parser = argparse.ArgumentParser(description="Analyze discussion intents using local clustering.")
    parser.add_argument("--input", default="discussions.json", help="Input JSON file path")
    parser.add_argument("--output", default="discussions_analyzed.json", help="Output JSON file path")
    parser.add_argument("--clusters", type=int, default=8, help="Number of clusters")
    args = parser.parse_args()

    print(f"Loading data from {args.input}...")
    data = load_data(args.input)
    
    # Prepare text for clustering
    documents = []
    valid_indices = []
    
    for i, item in enumerate(data):
        text = (item.get('title', '') + " " + item.get('content', ''))
        cleaned = clean_text(text)
        if len(cleaned) > 10:
            documents.append(cleaned)
            valid_indices.append(i)
            
    print(f"Vectorizing {len(documents)} documents...")
    vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
    X = vectorizer.fit_transform(documents)
    
    print(f"Clustering into {args.clusters} topics...")
    kmeans = KMeans(n_clusters=args.clusters, random_state=42)
    kmeans.fit(X)
    
    # Get cluster keywords
    print("Identifying cluster themes...")
    feature_names = vectorizer.get_feature_names_out()
    cluster_names = {}
    
    for i in range(args.clusters):
        center = kmeans.cluster_centers_[i]
        top_ind = center.argsort()[:-6:-1]
        keywords = [feature_names[ind] for ind in top_ind]
        cluster_names[i] = f"Topic: {', '.join(keywords)}"
        print(f"Cluster {i}: {', '.join(keywords)}")

    # Assign results back to data
    print("Tagging data...")
    for idx, doc_idx in enumerate(valid_indices):
        cluster_id = kmeans.labels_[idx]
        item = data[doc_idx]
        
        full_text = (item.get('title', '') + " " + item.get('content', ''))
        
        analysis = {
            "category": cluster_names[cluster_id],
            "product_area": get_product_area(full_text),
            "sentiment": analyze_sentiment_keyword(full_text),
            "pain_points": [], # Hard to extract specific points without LLM
            "summary": item.get('title', '') # Use title as summary fallback
        }
        
        item['analysis'] = analysis

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"Analysis complete. Saved to {args.output}")

if __name__ == "__main__":
    main()
