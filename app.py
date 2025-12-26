import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px
import subprocess
import sys

st.set_page_config(page_title="Copilot Feedback Analysis", layout="wide")

st.title("Microsoft 365 Copilot Feedback Analysis")

# --- Sidebar: Scraper Management ---
st.sidebar.header("Scraper Management")
with st.sidebar.expander("Run Scraper"):
    default_urls = "https://techcommunity.microsoft.com/category/microsoft365copilot/discussions/microsoft365copilot, https://techcommunity.microsoft.com/category/microsoft365/discussions/admincenter"
    urls_input = st.text_area("URLs to Scrape (comma separated)", value=default_urls, height=100)
    
    max_pages = st.number_input("Max Pages per Board (0 for unlimited)", min_value=0, value=10, step=1, help="Limit the number of pages to scrape per board. Useful for incremental updates.")

    if st.button("Run Scraper Now"):
        st.info("Scraper started. Streaming logs below...")
        log_placeholder = st.empty()
        full_logs = []
        
        try:
            # Construct command
            cmd = [
                sys.executable, "-m", "scrapy", "crawl", "techcommunity", 
                "-a", f"urls={urls_input}"
            ]
            
            if max_pages > 0:
                cmd.extend(["-a", f"max_pages={max_pages}"])
            
            # Run process with Popen for real-time output
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, # Merge stderr into stdout
                text=True,
                bufsize=1, # Line buffered
                encoding='utf-8',
                errors='replace'
            )
            
            # Read output line by line
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    full_logs.append(line)
                    # Update logs every few lines or just show the last 20 lines to avoid UI lag
                    # We join the last 20 lines for the preview, but keep full logs
                    log_preview = "".join(full_logs[-20:])
                    log_placeholder.code(log_preview, language="text")
            
            rc = process.poll()
            
            if rc == 0:
                st.success("Scraper finished successfully!")
                # Clear cache to ensure new data is loaded
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(f"Scraper failed with return code {rc}.")
            
            # Show full logs in an expander at the end
            with st.expander("View Full Scraper Logs"):
                st.code("".join(full_logs))
                
        except Exception as e:
            st.error(f"An error occurred: {e}")

with st.sidebar.expander("Run Analysis"):
    st.write("Run local keyword-based analysis to categorize discussions and determine sentiment.")
    if st.button("Run Analysis Now"):
        st.info("Analysis started...")
        try:
            result = subprocess.run(
                [sys.executable, "analyze_local.py"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                st.success("Analysis finished successfully!")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("Analysis failed.")
                st.code(result.stderr)
        except Exception as e:
            st.error(f"An error occurred: {e}")

# Load data
@st.cache_data
def load_data():
    db_path = "discussions.db"
    if not os.path.exists(db_path):
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
            "analysis_sentiment": "sentiment",
            "analysis_intent": "intent",
            "analysis_author_role": "author_role"
        }
        df = df.rename(columns=column_mapping)
        
        # Normalize sub_source to lowercase to merge duplicates
        if "sub_source" in df.columns:
            df["sub_source"] = df["sub_source"].str.lower()

        return df
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No data found. Please run the scraper first (or the analysis script).")
else:
    # Filters
    st.sidebar.header("Filters")
    
    filtered_df = df.copy()

    # Platform Filter
    if "platform" in filtered_df.columns:
        platforms = ["All"] + sorted(filtered_df["platform"].dropna().unique().tolist())
        selected_platform = st.sidebar.selectbox("Platform", platforms)
        if selected_platform != "All":
            filtered_df = filtered_df[filtered_df["platform"] == selected_platform]

    # Sub-source Filter
    if "sub_source" in filtered_df.columns:
        # Filter sub-sources based on selected platform if applicable
        available_sub_sources = filtered_df["sub_source"].dropna().unique().tolist()
        sub_sources = ["All"] + sorted(available_sub_sources)
        selected_sub_source = st.sidebar.selectbox("Sub-source (Board/Subreddit)", sub_sources)
        if selected_sub_source != "All":
            filtered_df = filtered_df[filtered_df["sub_source"] == selected_sub_source]

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

    # Intent Filter (if analyzed)
    if "intent" in filtered_df.columns:
        intents = ["All"] + sorted(filtered_df["intent"].dropna().unique().tolist())
        selected_intent = st.sidebar.selectbox("User Intent", intents)
        if selected_intent != "All":
            filtered_df = filtered_df[filtered_df["intent"] == selected_intent]

    # Author Role Filter (if analyzed)
    if "author_role" in filtered_df.columns:
        roles = ["All"] + sorted(filtered_df["author_role"].dropna().unique().tolist())
        selected_role = st.sidebar.selectbox("Author Role", roles)
        if selected_role != "All":
            filtered_df = filtered_df[filtered_df["author_role"] == selected_role]

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Discussions", len(filtered_df))
    col2.metric("Unique Authors", filtered_df["author"].nunique() if "author" in filtered_df.columns else 0)
    
    if "publish_date" in filtered_df.columns:
        latest_date = filtered_df["publish_date"].max()
        if pd.notnull(latest_date):
            col3.metric("Latest Post", latest_date.strftime("%Y-%m-%d"))

    # Analysis Metrics (if available)
    has_analysis = "sentiment" in filtered_df.columns
    if has_analysis:
        neg_sentiment = len(filtered_df[filtered_df["sentiment"] == "Negative"])
        total_count = len(filtered_df)
        percentage = (neg_sentiment / total_count) if total_count > 0 else 0
        col4.metric("Negative Sentiment", f"{neg_sentiment} ({percentage:.1%})")

    # Visualizations
    if not filtered_df.empty:
        st.subheader("Insights")
        
        # Row 1: Platform & Source Distribution
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            if "platform" in filtered_df.columns:
                fig_plat = px.pie(filtered_df, names="platform", title="Discussions by Platform", hole=0.4)
                st.plotly_chart(fig_plat, use_container_width=True)
        with r1c2:
            if "sub_source" in filtered_df.columns:
                # Top 10 sources
                source_counts = filtered_df["sub_source"].value_counts().head(10).reset_index()
                source_counts.columns = ["sub_source", "count"]
                fig_source = px.bar(source_counts, x="sub_source", y="count", title="Top Data Sources", color="sub_source")
                st.plotly_chart(fig_source, use_container_width=True)

        # Row 2: Analysis Charts (if available)
        if has_analysis:
            r2c1, r2c2 = st.columns(2)
            with r2c1:
                if "product_area" in filtered_df.columns:
                    fig_prod = px.pie(filtered_df, names="product_area", title="Discussions by Product Area")
                    st.plotly_chart(fig_prod, use_container_width=True)
            
            with r2c2:
                if "sentiment" in filtered_df.columns:
                    fig_sent = px.bar(filtered_df, x="sentiment", title="Sentiment Distribution", color="sentiment")
                    st.plotly_chart(fig_sent, use_container_width=True)

            # Row 3: Intent & Author Role
            r3c1, r3c2 = st.columns(2)
            with r3c1:
                if "intent" in filtered_df.columns:
                    fig_intent = px.pie(filtered_df, names="intent", title="User Intent Distribution", hole=0.4)
                    st.plotly_chart(fig_intent, use_container_width=True)
            
            with r3c2:
                if "author_role" in filtered_df.columns:
                    fig_role = px.pie(filtered_df, names="author_role", title="Author Role Distribution", hole=0.4)
                    st.plotly_chart(fig_role, use_container_width=True)

    # Display Data
    st.subheader("Discussions List")
    
    # Configure columns for display
    display_cols = ["platform", "sub_source", "title", "author", "publish_date", "reply_count"]
    if has_analysis:
        display_cols.extend(["category", "product_area", "sentiment", "intent", "author_role"])
    
    display_cols = [c for c in display_cols if c in df.columns]
    
    st.info("💡 **Tip:** Click the checkbox on the left of a row to view discussion details below.")

    selection = st.dataframe(
        filtered_df[display_cols],
        column_config={
            "publish_date": st.column_config.DatetimeColumn("Date", format="D MMM YYYY"),
            "reply_count": st.column_config.NumberColumn("Replies"),
            "platform": "Platform",
            "sub_source": "Source"
        },
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    # Detail View
    st.subheader("Discussion Details")
    
    if selection.selection.rows:
        selected_row_index = selection.selection.rows[0]
        item = filtered_df.iloc[selected_row_index]
        
        st.markdown(f"### [{item['title']}]({item.get('discussion_url', '#')})")
        st.markdown(f"**Author:** {item.get('author', 'Unknown')} | **Date:** {item.get('publish_date', 'Unknown')}")
        
        if has_analysis:
            st.info(f"**Category:** {item.get('category')} | **Product:** {item.get('product_area')} | **Sentiment:** {item.get('sentiment')} | **Intent:** {item.get('intent')} | **Role:** {item.get('author_role')}")
            if "pain_points" in item and item["pain_points"]:
                st.markdown("**Pain Points:**")
                for pp in item["pain_points"]:
                    st.markdown(f"- {pp}")
            if "summary" in item:
                st.markdown(f"**Summary:** {item['summary']}")

        with st.expander("Full Content", expanded=True):
            st.write(item.get("content", ""))

        if "replies" in item and isinstance(item["replies"], list):
            st.markdown(f"#### Replies ({len(item['replies'])})")
            for reply in item["replies"]:
                st.markdown("---")
                st.markdown(f"**{reply.get('author', 'Unknown')}** ({reply.get('publish_date', '')})")
                st.write(reply.get("content", ""))
    else:
        st.info("Select the checkbox next to a discussion to view details.")

