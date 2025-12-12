import sqlite3
import pandas as pd
import os

def load_data():
    db_path = "discussions.db"
    if not os.path.exists(db_path):
        print("DB not found")
        return pd.DataFrame()
        
    try:
        conn = sqlite3.connect(db_path)
        query = "SELECT * FROM discussions"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Convert date
        if "publish_date" in df.columns:
            df["publish_date"] = pd.to_datetime(df["publish_date"], errors='coerce')
            
        # Rename analysis columns to match expected format
        column_mapping = {
            "analysis_category": "category",
            "analysis_product_area": "product_area",
            "analysis_sentiment": "sentiment"
        }
        df = df.rename(columns=column_mapping)
        
        return df
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()

df = load_data()
print(f"Data loaded: {len(df)} rows")
print(f"Columns: {df.columns.tolist()}")
if not df.empty:
    print(f"Sample sentiment: {df['sentiment'].iloc[0]}")
    print(f"Sample category: {df['category'].iloc[0]}")
