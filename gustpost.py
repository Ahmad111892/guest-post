# app.py

import streamlit as st
import requests
import time
import pandas as pd
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json
from urllib.parse import urlparse
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
import random
import whois

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="🚀 ULTIMATE Guest Posting Finder",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR UI ENHANCEMENT ---
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 2rem;
    }
    .metric-card {
        background: #FFFFFF; padding: 1.5rem; border-radius: 10px; color: #333;
        text-align: center; border: 1px solid #E0E0E0; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .success-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1.5rem; border-radius: 10px; color: white; margin: 1rem 0;
    }
    .warning-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem; border-radius: 10px; color: white; margin: 1rem 0;
    }
    .stButton>button { width: 100%; }
</style>
""", unsafe_allow_html=True)


# --- CORE APPLICATION CLASS ---
class UltimateGuestPostingFinder:
    def __init__(self):
        self.ultimate_patterns = {
            'basic_footprints': ['"{niche}" "write for us"', '"{niche}" "guest post"'],
            'advanced_footprints': ['"{niche}" inurl:write-for-us', '"{niche}" inurl:contribute'],
            'title_patterns': ['"{niche}" intitle:"write for us"', '"{niche}" intitle:"guest post"'],
            'industry_specific': ['"{niche}" "accepting guest posts"', '"{niche}" "looking for contributors"'],
        }
        self.ultimate_indicators = {
            'platinum': ['write for us', 'guest posting guidelines', 'submission guidelines'],
            'gold': ['guest post', 'submit guest post', 'guest author'],
            'silver': ['contributor', 'submit content', 'collaborate with us'],
        }
        # Load API keys from Streamlit Secrets
        try:
            self.api_key = st.secrets["GOOGLE_API_KEY"]
            self.search_engine_id = st.secrets["SEARCH_ENGINE_ID"]
        except (FileNotFoundError, KeyError):
            self.api_key = None
            self.search_engine_id = None

    def generate_ultimate_queries(self, niche, competitors=None, location=None):
        all_queries = set()
        for patterns in self.ultimate_patterns.values():
            for pattern in patterns:
                all_queries.add(pattern.format(niche=niche))
        if location: all_queries.add(f'"{niche}" "{location}" "write for us"')
        if competitors:
            for competitor in competitors:
                if competitor: all_queries.add(f'"{competitor}" "guest post by" -site:{competitor}')
        return list(all_queries)

    def search_google_api(self, query):
        """
        PRIMARY AND ONLY SEARCH METHOD.
        Uses the reliable Google Programmable Search Engine API.
        """
        if not self.api_key or not self.search_engine_id:
            st.error("API Key or Search Engine ID is not configured in Streamlit Secrets.")
            return []

        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': query,
            'num': 10  # API allows max 10 results per query
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors or exceeding quota
            if 'error' in data:
                st.error(f"API Error: {data['error']['message']}")
                return []
                
            links = [item.get('link', '') for item in data.get('items', [])]
            return [link for link in links if self.is_valid_url(link)]
        except requests.RequestException as e:
            st.warning(f"API call failed. Error: {e}")
            return []

    def is_valid_url(self, url):
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]): return False
            blocked = ['google.com', 'youtube.com', 'facebook.com', 'twitter.com', 'wikipedia.org']
            return not any(b in parsed.netloc for b in blocked)
        except:
            return False

    def get_domain_age_score(self, domain):
        try:
            domain_info = whois.whois(domain)
            creation_date = domain_info.creation_date
            if isinstance(creation_date, list): creation_date = creation_date[0]
            if creation_date:
                age = (datetime.now() - creation_date).days / 365.25
                if age > 10: return 15
                elif age > 5: return 10
                elif age > 2: return 5
        except Exception: pass
        return 2

    def analyze_website(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text().lower()
            
            analysis = {
                'url': url, 'domain': urlparse(url).netloc,
                'title': soup.title.string.strip() if soup.title and soup.title.string else "No Title",
                'indicators_found': self.find_guest_posting_indicators(page_text),
                'emails': list(set(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', response.text))),
                'https_enabled': url.startswith('https://'),
            }
            
            analysis = self.calculate_all_scores(analysis)
            return analysis
        except Exception:
            return None

    def find_guest_posting_indicators(self, page_text):
        found = []
        for confidence, indicators in self.ultimate_indicators.items():
            for indicator in indicators:
                if indicator in page_text:
                    found.append({'text': indicator, 'confidence': confidence})
        return found

    def calculate_all_scores(self, analysis):
        score = sum({'platinum': 25, 'gold': 15, 'silver': 10}.get(ind['confidence'], 0) for ind in analysis['indicators_found'])
        analysis['confidence_score'] = min(score, 100)
        
        da_score = self.get_domain_age_score(analysis['domain']) + (15 if analysis['https_enabled'] else 0)
        if any(tld in analysis['domain'] for tld in ['.edu', '.gov']): da_score += 25
        analysis['domain_authority'] = min(int(da_score * 2.0), 100)

        analysis['trust_score'] = min((30 if analysis['emails'] else 0) + (20 if analysis['https_enabled'] else 0) + (15 if analysis['domain_authority'] > 50 else 5), 100)
        return analysis

    def parallel_search_and_analyze(self, niche, competitors, location, max_sites):
        st.info("🚀 Initiating ULTIMATE search using the Google API...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_queries = self.generate_ultimate_queries(niche, competitors, location)
        all_urls = set()
        
        # The free API is limited to 100 queries/day, so we use them efficiently
        queries_to_run = all_queries[:15] # Limit to 15 API calls per run to be safe
        
        with ThreadPoolExecutor(max_workers=5) as executor: # Lower workers for API politeness
            futures = {executor.submit(self.search_google_api, query) for query in queries_to_run}
            for i, future in enumerate(as_completed(futures)):
                all_urls.update(future.result())
                progress_bar.progress(int(((i + 1) / len(futures)) * 50))
                status_text.text(f"🔍 Searching... Found {len(all_urls)} potential sites from {i+1}/{len(futures)} queries.")
        
        st.session_state.search_stats['urls_found'] = len(all_urls)
        unique_urls = list(all_urls)
        
        if not unique_urls:
            status_text.error("Search phase completed but found 0 URLs. Check if your API quota is exceeded.")
            return []

        status_text.text(f"🔬 Found {len(unique_urls)} unique URLs. Starting deep analysis...")
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            analysis_futures = {executor.submit(self.analyze_website, url) for url in unique_urls}
            for i, future in enumerate(as_completed(analysis_futures)):
                result = future.result()
                if result: results.append(result)
                progress_bar.progress(50 + int(((i + 1) / len(analysis_futures)) * 50))
                status_text.text(f"🔬 Analyzing... {i+1}/{len(analysis_futures)} sites processed.")
        
        st.session_state.search_stats['sites_analyzed'] = len(results)
        filtered_results = [r for r in results if r.get('confidence_score', 0) > 0]
        filtered_results.sort(key=lambda x: (x.get('confidence_score', 0) * 0.6 + x.get('domain_authority', 0) * 0.4), reverse=True)
        
        final_results = filtered_results[:max_sites]
        status_text.success(f"✅ ULTIMATE analysis complete! Found {len(final_results)} guest posting opportunities.")
        return final_results

# --- UI AND DASHBOARD FUNCTIONS ---
def show_api_setup_instructions():
    st.error("API Key or Search Engine ID not found!")
    st.markdown("""
    ### 🔑 One-Time Setup Required (5 Minutes)
    To use this tool reliably, you need a free Google API Key and a Programmable Search Engine ID.

    **Step 1: Get Your API Key**
    1.  Go to the [Google Cloud Console Credentials Page](https://console.cloud.google.com/apis/credentials).
    2.  Create a new project (or select an existing one).
    3.  Click **"+ CREATE CREDENTIALS"** and select **"API key"**.
    4.  Copy your new API key. **Do not add any restrictions.**

    **Step 2: Get Your Programmable Search Engine ID**
    1.  Go to the [Programmable Search Engine Control Panel](https://programmablesearchengine.google.com/controlpanel/all).
    2.  Click **"Add"** to create a new search engine.
    3.  Under "What to search?", select **"Search the entire web"**.
    4.  Give it a name (e.g., "GuestPostFinder") and click **"Create"**.
    5.  Copy your **"Search engine ID"** from the main page.

    **Step 3: Add Keys to Streamlit Secrets**
    1.  In your app, click **"Manage app"** -> **"Secrets"**.
    2.  Paste the following and replace the placeholders:
        ```toml
        # secrets.toml
        GOOGLE_API_KEY = "PASTE_YOUR_API_KEY_HERE"
        SEARCH_ENGINE_ID = "PASTE_YOUR_SEARCH_ENGINE_ID_HERE"
        ```
    3.  Click **"Save"**. The app will reboot.
    """)

# --- MAIN APPLICATION LOGIC ---
def main():
    st.markdown('<div class="main-header"><h1>🚀 ULTIMATE Guest Posting Finder</h1><p>A Reliable AI-Powered Discovery System</p></div>', unsafe_allow_html=True)
    
    if 'finder' not in st.session_state:
        st.session_state.finder = UltimateGuestPostingFinder()

    finder = st.session_state.finder

    if not finder.api_key or not finder.search_engine_id:
        show_api_setup_instructions()
        st.stop()

    with st.sidebar:
        st.markdown("### ⚙️ ULTIMATE Configuration")
        niche = st.text_input("🎯 Your Niche/Industry", placeholder="e.g., health, technology, finance")
        st.markdown("#### 🔧 Advanced Options (Optional)")
        competitors = [c.strip() for c in st.text_area("🏆 Competitor Websites", placeholder="competitor1.com\ncompetitor2.com").split('\n') if c.strip()]
        location = st.text_input("🌍 Geographic Focus", placeholder="e.g., USA, UK, Canada")
        max_sites = st.slider("🎯 Maximum Sites to Find", 10, 100, 50)
        search_button = st.button("🚀 START ULTIMATE SEARCH", type="primary")
    
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'search_stats' not in st.session_state:
        st.session_state.search_stats = {'urls_found': 0, 'sites_analyzed': 0}

    if search_button:
        if not niche:
            st.error("🚫 Please enter your niche/industry to begin the search.")
        else:
            st.session_state.search_stats = {'urls_found': 0, 'sites_analyzed': 0}
            st.session_state.results = finder.parallel_search_and_analyze(niche, competitors, location, max_sites)
    
    if st.session_state.results is not None:
        results = st.session_state.results
        if results:
            st.markdown(f'<div class="success-card"><h3>🎉 ULTIMATE Search Complete!</h3><p>Found <strong>{len(results)}</strong> high-quality opportunities for "<strong>{niche}</strong>".</p></div>', unsafe_allow_html=True)
            
            # Display results in tabs
            tab1, tab2 = st.tabs(["🎯 Premium Results", "📥 Export Hub"])
            with tab1:
                for i, result in enumerate(results):
                    with st.expander(f"🏆 #{i+1} - {result.get('title', 'Unknown')} (DA: {result.get('domain_authority', 0)})"):
                        st.markdown(f"**🌐 URL:** [{result.get('domain', 'N/A')}]({result.get('url', '#')})")
                        if result.get('emails'): st.markdown(f"**📧 Contact Emails:** {', '.join(result.get('emails', []))}")
            with tab2:
                 # Simplified export options
                df_export = pd.DataFrame(results)
                st.download_button(label="📊 Download as CSV", data=df_export.to_csv(index=False).encode('utf-8'), file_name="guest_post_sites.csv")
        else:
            stats = st.session_state.search_stats
            st.markdown(f'''
            <div class="warning-card">
                <h3>🔍 No Results Found</h3>
                <p>Your search returned no opportunities. Here is a summary:</p>
                <ul>
                    <li>Potential URLs found: <strong>{stats.get("urls_found", 0)}</strong></li>
                    <li>Sites that passed analysis: <strong>{stats.get("sites_analyzed", 0)}</strong></li>
                </ul>
                <p><strong>Suggestions:</strong></p>
                <ul>
                    <li>Check your API daily quota on the Google Cloud Console.</li>
                    <li>Use a broader niche term.</li>
                </ul>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.info("💡 Enter your niche in the sidebar and click 'START' to discover opportunities.")

    st.markdown("<div style='text-align: center; color: #888; padding-top: 2rem;'><p><strong>🚀 ULTIMATE Guest Posting Finder</strong></p></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
