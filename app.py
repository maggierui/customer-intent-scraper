import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px

st.set_page_config(page_title="Copilot Feedback Analysis", layout="wide")

st.title("Microsoft 365 Copilot Feedback Analysis")

# Load data
@st.cache_data
def load_data():
    # Prioritize analyzed data, fallback to raw data
    data_files = ["discussions_analyzed.json", "discussions.json"]
    
    for file in data_files:
        if os.path.exists(file):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                df = pd.DataFrame(data)
                
                # Normalize analysis column if it exists (flatten the JSON)
                if "analysis" in df.columns and not df["analysis"].isna().all():
                    # Handle cases where analysis might be None for some rows
                    analysis_data = df["analysis"].apply(lambda x: x if isinstance(x, dict) else {})
                    analysis_df = pd.json_normalize(analysis_data)
                    df = pd.concat([df.drop(columns=["analysis"]), analysis_df], axis=1)
                
                # Convert date
                if "publish_date" in df.columns:
                    df["publish_date"] = pd.to_datetime(df["publish_date"], errors='coerce')
                    
                return df
            except Exception as e:
                st.error(f"Error loading {file}: {e}")
    
    return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No data found. Please run the scraper first (or the analysis script).")
else:
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Discussions", len(df))
    col2.metric("Unique Authors", df["author"].nunique() if "author" in df.columns else 0)
    
    if "publish_date" in df.columns:
        latest_date = df["publish_date"].max()
        if pd.notnull(latest_date):
            col3.metric("Latest Post", latest_date.strftime("%Y-%m-%d"))

    # Analysis Metrics (if available)
    has_analysis = "sentiment" in df.columns
    if has_analysis:
        neg_sentiment = len(df[df["sentiment"] == "Negative"])
        col4.metric("Negative Sentiment", f"{neg_sentiment} ({neg_sentiment/len(df):.1%})")

    # Filters
    st.sidebar.header("Filters")
    
    filtered_df = df.copy()

    # Search
    search_term = st.sidebar.text_input("Search (Title/Content)")
    if search_term:
        filtered_df = filtered_df[
            filtered_df["title"].str.contains(search_term, case=False, na=False) | 
            filtered_df["content"].str.contains(search_term, case=False, na=False)
        ]

    # Category Filter (if analyzed)
    if "category" in filtered_df.columns:
        categories = ["All"] + sorted(filtered_df["category"].dropna().unique().tolist())
        selected_category = st.sidebar.selectbox("Category", categories)
        if selected_category != "All":
            filtered_df = filtered_df[filtered_df["category"] == selected_category]

    # Product Area Filter (if analyzed)
    if "product_area" in filtered_df.columns:
        products = ["All"] + sorted(filtered_df["product_area"].dropna().unique().tolist())
        selected_product = st.sidebar.selectbox("Product Area", products)
        if selected_product != "All":
            filtered_df = filtered_df[filtered_df["product_area"] == selected_product]

    # Visualizations
    if has_analysis and not filtered_df.empty:
        st.subheader("Insights")
        c1, c2 = st.columns(2)
        
        with c1:
            if "product_area" in filtered_df.columns:
                fig_prod = px.pie(filtered_df, names="product_area", title="Discussions by Product Area")
                st.plotly_chart(fig_prod, use_container_width=True)
        
        with c2:
            if "sentiment" in filtered_df.columns:
                fig_sent = px.bar(filtered_df, x="sentiment", title="Sentiment Distribution", color="sentiment")
                st.plotly_chart(fig_sent, use_container_width=True)

    # Display Data
    st.subheader("Discussions List")
    
    # Configure columns for display
    display_cols = ["title", "author", "publish_date", "reply_count"]
    if has_analysis:
        display_cols.extend(["category", "product_area", "sentiment"])
    
    display_cols = [c for c in display_cols if c in df.columns]
    
    st.dataframe(
        filtered_df[display_cols],
        column_config={
            "publish_date": st.column_config.DatetimeColumn("Date", format="D MMM YYYY"),
            "reply_count": st.column_config.NumberColumn("Replies"),
        },
        use_container_width=True,
        hide_index=True
    )

    # Detail View
    st.subheader("Discussion Details")
    selected_idx = st.selectbox("Select a discussion to view details:", filtered_df.index, format_func=lambda x: filtered_df.loc[x, "title"][:100])
    
    if selected_idx is not None:
        item = filtered_df.loc[selected_idx]
        st.markdown(f"### [{item['title']}]({item.get('discussion_url', '#')})")
        st.markdown(f"**Author:** {item.get('author', 'Unknown')} | **Date:** {item.get('publish_date', 'Unknown')}")
        
        if has_analysis:
            st.info(f"**Category:** {item.get('category')} | **Product:** {item.get('product_area')} | **Sentiment:** {item.get('sentiment')}")
            if "pain_points" in item and item["pain_points"]:
                st.markdown("**Pain Points:**")
                for pp in item["pain_points"]:
                    st.markdown(f"- {pp}")
            if "summary" in item:
                st.markdown(f"**Summary:** {item['summary']}")

        with st.expander("Full Content"):
            st.write(item.get("content", ""))

        if "replies" in item and isinstance(item["replies"], list):
            st.markdown(f"#### Replies ({len(item['replies'])})")
            for reply in item["replies"]:
                st.markdown("---")
                st.markdown(f"**{reply.get('author', 'Unknown')}** ({reply.get('publish_date', '')})")
                st.write(reply.get("content", ""))

