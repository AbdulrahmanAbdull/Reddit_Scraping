#v1

import streamlit as st
import praw
import gspread
import datetime
import re
from oauth2client.service_account import ServiceAccountCredentials

# Reddit API credentials
REDDIT_CLIENT_ID = "lWFWfRPV8_EHqjRpAdzclA"
REDDIT_CLIENT_SECRET = "TUfF3yHH80wYOSCvtXajFQ9QkblXmQ"
REDDIT_USER_AGENT = "scraping"

# Google Sheets authentication using Streamlit secrets
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = st.secrets["google_creds_file"]

# Streamlit UI
st.title("Reddit Scraper")

# Load saved input
if 'saved_url' not in st.session_state:
    st.session_state['saved_url'] = ""
if 'saved_keywords' not in st.session_state:
    st.session_state['saved_keywords'] = ""

# Input fields
url_input = st.text_area("Enter subreddit links (one per line)", value=st.session_state['saved_url'])
keyword_input = st.text_area("Enter keywords (comma-separated)", value=st.session_state['saved_keywords'])

# Buttons for actions
if st.button("Save Input"):
    st.session_state['saved_url'] = url_input
    st.session_state['saved_keywords'] = keyword_input
    st.success("Input saved.")

if st.button("Reset"):
    st.session_state['saved_url'] = ""
    st.session_state['saved_keywords'] = ""
    st.success("Input reset.")

#if st.button("Restart"):
   # st.experimental_rerun()

if st.button("Start"):
    # Initialize Reddit API
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )

    # Google Sheets connection
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_creds_file"], SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open("redditData").sheet1

    # Process input
    subreddit_urls = [link.strip() for link in url_input.splitlines() if link.strip()]
    keywords = [kw.strip().lower() for kw in keyword_input.split(',') if kw.strip()]
    keyword_urls = [f"https://www.reddit.com/r/{kw}" for kw in keywords]

    all_urls = subreddit_urls + keyword_urls

    # Generate regex patterns for contextual matching
    keyword_patterns = [re.compile(rf"\b{re.escape(kw)}(s|es|ks|ks'|es'|s'|ing|ed)?\b", re.IGNORECASE) for kw in keywords]

    all_posts_data = []

    # Handling keyword variations
    for kw in keywords:
        variations = [kw, f"{kw}s", f"{kw}es", f"{kw}ks", f"{kw}ing", f"{kw}ed"]
        for var in variations:
            url = f"https://www.reddit.com/r/{var}"
            if url not in all_urls:
                all_urls.append(url)

    # Fetch existing data from Google Sheets
    existing_records = sheet.get_all_values()
    existing_links = {row[3] for row in existing_records[1:]}  # Assuming permalink is in the 4th column

    for url in all_urls:
        subreddit_name = url.replace("https://www.reddit.com/r/", "").strip('/')
        try:
            subreddit = reddit.subreddit(subreddit_name)

            for post in subreddit.new(limit=None):
                matched_keywords = [kw for pattern, kw in zip(keyword_patterns, keywords) if pattern.search(post.title)]
                post_permalink = f"https://www.reddit.com{post.permalink}"

                if post_permalink not in existing_links:
                    post_info = [
                        subreddit_name,
                        url,
                        post.title,
                        post_permalink,
                        post.score,
                        datetime.datetime.fromtimestamp(post.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                        ", ".join(matched_keywords)
                    ]
                    all_posts_data.append(post_info)

        except Exception:
            pass

    if all_posts_data:



    
        sheet.append_rows(all_posts_data, value_input_option="RAW")
        st.success(f"Successfully saved {len(all_posts_data)} new posts to Google Sheets.")
    else:
        st.warning("No new posts to save.")


