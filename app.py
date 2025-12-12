import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="Tech Community Scraper", layout="wide")

st.title("Microsoft Tech Community Discussions")

# Load data
@st.cache_data
def load_data():
    if not os.path.exists("all_discussions.jsonl"):
        return pd.DataFrame()
    
    try:
        data = []
        with open("all_discussions.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data.append(json.loads(line))
                except:
                    continue
        
        df = pd.DataFrame(data)
        
        # Convert date
        if "publish_date" in df.columns:
            df["publish_date"] = pd.to_datetime(df["publish_date"])
            
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No data found. Please run the scraper first.")
else:
    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Discussions", len(df))
    col2.metric("Unique Authors", df["author"].nunique() if "author" in df.columns else 0)
    
    if "publish_date" in df.columns:
        latest_date = df["publish_date"].max()
        col3.metric("Latest Post", latest_date.strftime("%Y-%m-%d"))

    # Filters
    st.sidebar.header("Filters")
    search_term = st.sidebar.text_input("Search (Title/Content)")
    
    filtered_df = df.copy()
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df["title"].str.contains(search_term, case=False, na=False) | 
            filtered_df["content"].str.contains(search_term, case=False, na=False)
        ]

    # Display Data
    st.subheader("Discussions")
    
    # Configure columns for display
    display_cols = ["title", "author", "publish_date", "discussion_url"]
    display_cols = [c for c in display_cols if c in df.columns]
    
    st.dataframe(
        filtered_df[display_cols],
        column_config={
            "discussion_url": st.column_config.LinkColumn("Link"),
            "publish_date": st.column_config.DatetimeColumn("Date", format="D MMM YYYY, h:mm a"),
        },
        use_container_width=True,
        hide_index=True
    )

    # Raw Data Expander
    with st.expander("View Raw Data"):
        st.json(filtered_df.to_dict(orient="records"))
