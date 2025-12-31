# Customer Intent Scraper & Analyzer

Welcome to the **Customer Intent Scraper**! 🚀

This project is a tool designed to "listen" to what people are saying about Microsoft products (like Copilot, SharePoint, Teams) on online forums. It collects discussions, analyzes them to understand how people feel and what they need, and presents everything in an easy-to-use dashboard.

Think of it as a **feedback engine**: it gathers raw comments, processes them to find patterns, and shows you the big picture.

---

## 🛠️ Technologies Used

This project is built using **Python** and uses several powerful libraries:

*   **[Scrapy](https://scrapy.org/)**: A fast web crawling framework used to collect data from websites (like Microsoft Tech Community).
*   **[Streamlit](https://streamlit.io/)**: A library that turns Python scripts into shareable web apps. We use it for our dashboard.
*   **[SQLite](https://www.sqlite.org/index.html)**: A lightweight database to store all the discussions and analysis results.
*   **[scikit-learn](https://scikit-learn.org/)**: A machine learning library used here to group similar discussions together (clustering).
*   **[Pandas](https://pandas.pydata.org/)**: Used for organizing and filtering data (like an Excel spreadsheet in code).

---

## 📂 Project Structure

Here is a simple guide to the most important files in this project:

### 1. The Dashboard (`app.py`)
*   **Purpose**: This is the "face" of the application. It's what you see in your web browser.
*   **What it does**:
    *   **General Dashboard**: Displays charts and graphs (Sentiment, User Intent, Author Roles) and a searchable list of discussions.
    *   **Topic Explorer**: A deep-dive view that clusters discussions by topic and breaks them down by user role (IT Admin, Developer, End User), showing unique keywords for each perspective.
    *   Allows you to filter data (e.g., show only "Negative" feedback or "Feature Requests").
    *   Lets you trigger the **Scraper** and the **Analyzer** directly from the sidebar.

### 2. The Brain (`analyze_local.py`)
*   **Purpose**: This script does the thinking. It takes the raw text and makes sense of it.
*   **What it does**:
    *   **Sentiment Analysis**: Decides if a post is Positive, Negative, or Neutral.
    *   **Intent Detection**: Guesses if the user is reporting a bug, asking a question, or requesting a feature.
    *   **Role Identification**: Classifies the author as an **IT Admin**, **Developer**, or **End User** based on their vocabulary.
    *   **Product Detection**: Identifies which product (e.g., Excel, Teams) is being discussed.
    *   **Clustering**: Groups similar discussions into topics using machine learning (K-Means).

### 3. The Collector (`customer_intent_scraper/`)
*   **Purpose**: This folder contains the "spiders" that crawl the web.
*   **Key File**: `spiders/techcommunity.py`
    *   This script visits specific URLs, downloads the page content, extracts the title, author, date, and text, and saves it.

### 4. The Storage (`discussions.db`)
*   **Purpose**: The project's filing cabinet.
*   **What it does**: It's a database file that stores every discussion found. When you run the scraper, new rows are added here. When you run the analysis, existing rows are updated with new tags.

---

## 🚀 How It Works (The Workflow)

Imagine this process in three steps: **Collect**, **Process**, and **View**.

### Step 1: Collect (Scraping)
1.  Open the dashboard (`app.py`).
2.  In the sidebar, enter the URLs you want to scrape.
3.  Click **"Run Scraper Now"**.
4.  The program sends out "spiders" to fetch the latest discussions and saves them to the database.
    *   *Note: At this stage, the data is "raw". It doesn't know if a post is happy or sad yet.*

### Step 2: Process (Analysis)
1.  In the dashboard sidebar, go to the "Run Analysis" section.
2.  Click **"Run Analysis Now"**.
3.  The `analyze_local.py` script wakes up. It reads the new raw data, looks for keywords (like "error" for bugs, or "love" for positive sentiment), and updates the database with these new labels.

### Step 3: View (Dashboard)
1.  The dashboard refreshes.
2.  You can now see updated charts showing how many people are reporting bugs vs. asking questions.
3.  You can click on individual rows in the list to read the full discussion details.
4.  **New**: You can click the "Open" link in the table or the title in the details view to visit the actual online discussion.

---

## 💻 How to Run It

If you are a new collaborator, here is how to get started:

1.  **Install Requirements**:
    Make sure you have Python installed, then run:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Start the App**:
    Run the following command in your terminal:
    ```bash
    streamlit run app.py
    ```

3.  **Explore**:
    The app will open in your web browser (usually at `http://localhost:8501`).

---

## 🤝 Contributing

*   **Adding new keywords**: If you notice the analyzer is missing some product names or roles, edit the dictionaries in `analyze_local.py`.
*   **Improving the UI**: If you want to change how the data looks, edit `app.py`.
*   **New Data Sources**: To scrape a new website, you would add a new spider in `customer_intent_scraper/spiders/`.

Happy Coding! 🤖
