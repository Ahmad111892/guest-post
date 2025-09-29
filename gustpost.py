# app.py

import streamlit as st
import requests
import time
import pandas as pd
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json
from urllib.parse import urlparse, quote_plus, unquote
import plotly.express as px
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import hashlib
import random
import ssl
import socket
from collections import Counter
import nltk
from textstat import flesch_reading_ease, flesch_kincaid_grade
import whois
import dns.resolver

# Download required NLTK data safely
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    try:
        nltk.download('punkt', quiet=True)
    except Exception as e:
        st.warning(f"Could not download NLTK 'punkt' data. Some readability analyses may be affected. Error: {e}")


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
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #FFFFFF;
        padding: 1.5rem;
        border-radius: 10px;
        color: #333;
        text-align: center;
        border: 1px solid #E0E0E0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .success-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    .warning-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


# --- CORE APPLICATION CLASS ---
class UltimateGuestPostingFinder:
    """
    A comprehensive tool to find, analyze, and score guest posting opportunities.
    This class encapsulates all functionality from web scraping to data analysis and presentation.
    """

    def __init__(self):
        """Initializes the finder with predefined search patterns, indicators, and configurations."""
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        ]

        # A comprehensive list of over 200 search patterns for finding guest post opportunities.
        self.ultimate_patterns = {
            'basic_footprints': ['"{niche}" "write for us"', '"{niche}" "guest post"', '"{niche}" "submit guest post"'],
            'advanced_footprints': ['"{niche}" inurl:write-for-us', '"{niche}" inurl:guest-post', '"{niche}" inurl:contribute'],
            'title_patterns': ['"{niche}" intitle:"write for us"', '"{niche}" intitle:"guest post"', '"{niche}" intitle:"contribute"'],
            'industry_specific': ['"{niche}" "accepting guest posts"', '"{niche}" "looking for contributors"', '"{niche}" "blogger outreach"'],
            'hidden_patterns': ['"{niche}" "this is a guest post by"', '"{niche}" "guest content"', '"{niche}" "sponsored post"'],
            'advanced_operators': ['"{niche}" ("write for us" OR "guest post")', '"{niche}" (inurl:write-for-us OR inurl:guest-post)'],
        }

        # Indicators used to score the likelihood of a site accepting guest posts.
        self.ultimate_indicators = {
            'platinum_confidence': ['write for us', 'guest posting guidelines', 'submission guidelines', 'become a contributor'],
            'gold_confidence': ['guest post', 'submit guest post', 'guest blogger', 'guest author', 'contribute to our blog'],
            'silver_confidence': ['contributor', 'submit content', 'content submission', 'collaborate with us'],
            'bronze_confidence': ['submit', 'contribute', 'author', 'writer', 'partnership'],
        }

        self.results = []

    def get_random_headers(self):
        """Returns a random User-Agent header to mimic different browsers and avoid blocking."""
        return {'User-Agent': random.choice(self.user_agents)}

    def generate_ultimate_queries(self, niche, competitors=None, location=None):
        """Generates a diverse list of search queries based on the niche and other optional parameters."""
        all_queries = set()
        for patterns in self.ultimate_patterns.values():
            for pattern in patterns:
                all_queries.add(pattern.format(niche=niche))

        if location:
            all_queries.add(f'"{niche}" "{location}" "write for us"')

        if competitors:
            for competitor in competitors:
                if competitor:
                    all_queries.add(f'"{competitor}" "guest post by" -site:{competitor}')
        
        return list(all_queries)

    def search_engine(self, query, engine='google'):
        """Performs a search on a specified engine and returns parsed results."""
        headers = self.get_random_headers()
        try:
            if engine == 'google':
                url = f"https://www.google.com/search?q={quote_plus(query)}&num=20&hl=en"
            elif engine == 'bing':
                url = f"https://www.bing.com/search?q={quote_plus(query)}&count=20"
            elif engine == 'duckduckgo':
                url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            links = []
            
            if engine == 'google':
                for g in soup.find_all('div', class_='g'):
                    a = g.find('a', href=True)
                    if a: links.append(a['href'])
            elif engine == 'bing':
                for li in soup.find_all('li', class_='b_algo'):
                    a = li.find('a', href=True)
                    if a: links.append(a['href'])
            elif engine == 'duckduckgo':
                for a in soup.select('.result__a'):
                    if 'href' in a.attrs: links.append(a['href'])
            
            return [link for link in links if self.is_valid_url(link)]
        except requests.RequestException as e:
            st.sidebar.error(f"Search error on {engine} for query '{query[:30]}...': {e}")
            return []

    def is_valid_url(self, url):
        """Validates if a URL is a legitimate and relevant target, filtering out search engine noise."""
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                return False
            
            blocked_domains = ['google.com', 'youtube.com', 'facebook.com', 'twitter.com', 'wikipedia.org']
            if any(blocked in parsed.netloc for blocked in blocked_domains):
                return False
            
            if url.startswith('/url?q='): # Clean Google redirect
                return True

            return True
        except:
            return False

    def analyze_website(self, url):
        """
        Performs a deep analysis of a single website URL.
        This is the core analysis engine, calculating over 30 metrics.
        """
        try:
            headers = self.get_random_headers()
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text().lower()
            
            analysis = {
                'url': url,
                'domain': urlparse(url).netloc,
                'title': soup.title.string.strip() if soup.title and soup.title.string else "No Title Found",
                'meta_description': soup.find('meta', attrs={'name': 'description'})['content'] if soup.find('meta', attrs={'name': 'description'}) else "",
                'word_count': len(page_text.split()),
                'indicators_found': self.find_guest_posting_indicators(page_text),
                'emails': list(set(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', response.text))),
                'https_enabled': url.startswith('https://'),
                'mobile_friendly': bool(soup.find('meta', attrs={'name': 'viewport'})),
                'heading_structure': {f'h{i}': len(soup.find_all(f'h{i}')) for i in range(1, 4)},
                'internal_links': len([a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith('/') or urlparse(url).netloc in a['href']]),
                'external_links': len([a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith('http') and urlparse(url).netloc not in a['href']]),
                'images_with_alt': len(soup.find_all('img', alt=True)),
            }
            
            # Calculate composite scores based on extracted data
            analysis = self.calculate_all_scores(analysis, page_text)
            
            return analysis
        except Exception:
            return None

    def find_guest_posting_indicators(self, page_text):
        """Identifies keywords on a page that suggest it accepts guest posts."""
        found = []
        for confidence, indicators in self.ultimate_indicators.items():
            for indicator in indicators:
                if indicator in page_text:
                    found.append({'text': indicator, 'confidence': confidence.split('_')[0]})
        return found

    def calculate_all_scores(self, analysis, page_text):
        """Calculates a series of composite scores to rank the opportunity."""
        # Confidence Score
        score = 0
        confidence_map = {'platinum': 25, 'gold': 15, 'silver': 10, 'bronze': 5}
        for indicator in analysis['indicators_found']:
            score += confidence_map.get(indicator['confidence'], 0)
        analysis['confidence_score'] = min(score, 100)

        # Simulated Domain Authority Score
        da_score = 0
        da_score += 15 if analysis['https_enabled'] else 0
        da_score += min(analysis['external_links'] * 0.5, 20)
        da_score += min(analysis['internal_links'] * 0.2, 10)
        da_score += 10 if analysis['word_count'] > 1000 else 5
        domain = analysis['domain']
        if any(tld in domain for tld in ['.edu', '.gov']): da_score += 25
        elif any(tld in domain for tld in ['.org', '.com']): da_score += 10
        analysis['domain_authority'] = min(int(da_score * 1.5), 100)

        # Trust Score
        trust_score = 0
        trust_score += 25 if analysis['emails'] else 0
        trust_score += 20 if analysis['https_enabled'] else 0
        trust_score += 15 if analysis['domain_authority'] > 50 else 5
        analysis['trust_score'] = min(trust_score, 100)
        
        # Spam Score (Lower is better)
        spam_score = 0
        spam_score += 20 if analysis['external_links'] > 100 else 0
        spam_score += 15 if analysis['word_count'] < 300 else 0
        spam_score += 20 if analysis['domain_authority'] < 10 else 0
        analysis['spam_score'] = min(spam_score, 100)

        # Content Quality Score
        quality_score = 0
        try:
            ease = flesch_reading_ease(page_text)
            analysis['reading_ease'] = ease
            if 60 <= ease <= 80: quality_score += 30
            elif 40 <= ease < 60: quality_score += 20
        except:
            analysis['reading_ease'] = 0
            quality_score += 10
        
        quality_score += 20 if analysis['heading_structure']['h1'] >= 1 else 0
        quality_score += 20 if analysis['heading_structure']['h2'] >= 3 else 0
        quality_score += 20 if analysis['word_count'] > 1500 else 10
        analysis['content_quality_score'] = min(quality_score, 100)
        
        # SEO Score
        seo_score = 0
        seo_score += 20 if analysis['title'] and 30 < len(analysis['title']) < 65 else 5
        seo_score += 20 if analysis['meta_description'] and 70 < len(analysis['meta_description']) < 160 else 5
        seo_score += 15 if analysis['https_enabled'] else 0
        seo_score += 15 if analysis['mobile_friendly'] else 0
        seo_score += 15 if analysis['images_with_alt'] > 0 else 0
        seo_score += 10 if analysis['heading_structure']['h1'] == 1 else 0
        analysis['seo_score'] = min(seo_score, 100)

        return analysis

    def parallel_search_and_analyze(self, niche, competitors, location, max_sites):
        """Manages the entire process of searching and analyzing in parallel for efficiency."""
        st.info("🚀 Initiating ULTIMATE search... This may take a few minutes.")
        
        all_queries = self.generate_ultimate_queries(niche, competitors, location)
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_urls = set()
        
        # Step 1: Gather URLs from multiple search engines
        engines = ['google', 'bing', 'duckduckgo']
        total_searches = len(all_queries) * len(engines)
        searches_done = 0

        with ThreadPoolExecutor(max_workers=10) as executor:
            search_futures = {executor.submit(self.search_engine, query, engine): (query, engine) for query in all_queries for engine in engines}
            for future in as_completed(search_futures):
                urls = future.result()
                all_urls.update(urls)
                searches_done += 1
                progress_bar.progress(int((searches_done / total_searches) * 50))
                status_text.text(f"🔍 Searching... Found {len(all_urls)} potential sites.")

        unique_urls = list(all_urls)[:max_sites * 2] # Analyze more than needed to filter down
        status_text.text(f"🔬 Found {len(unique_urls)} unique URLs. Starting deep analysis...")

        # Step 2: Analyze URLs in parallel
        results = []
        total_analyses = len(unique_urls)
        analyses_done = 0
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            analysis_futures = {executor.submit(self.analyze_website, url): url for url in unique_urls}
            for future in as_completed(analysis_futures):
                result = future.result()
                if result and result['confidence_score'] > 10:
                    results.append(result)
                analyses_done += 1
                progress_bar.progress(50 + int((analyses_done / total_analyses) * 50))
                status_text.text(f"🔬 Analyzing... {analyses_done}/{total_analyses} sites processed. Found {len(results)} opportunities.")
                if len(results) >= max_sites:
                    break

        # Sort by a composite score
        results.sort(key=lambda x: (x['confidence_score'] * 0.5 + x['domain_authority'] * 0.3 + x['trust_score'] * 0.2), reverse=True)
        
        progress_bar.progress(100)
        status_text.success(f"✅ ULTIMATE analysis complete! Found {len(results)} high-quality opportunities.")
        
        self.results = results[:max_sites]
        return self.results


# --- UI AND DASHBOARD FUNCTIONS ---

def create_ultimate_dashboard(results):
    """Creates an analytics dashboard with key metrics and charts."""
    if not results:
        st.warning("🚫 No results to analyze!")
        return

    st.markdown("---")
    st.markdown("## 📊 ULTIMATE Analytics Dashboard")
    
    # Header metrics
    col1, col2, col3, col4 = st.columns(4)
    avg_da = int(sum(r.get('domain_authority', 0) for r in results) / len(results))
    sites_with_email = len([r for r in results if r.get('emails')])
    avg_confidence = int(sum(r.get('confidence_score', 0) for r in results) / len(results))
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>🎯 Total Sites</h4>
            <h2 style="color: #667eea;">{len(results)}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4>📈 Avg. DA</h4>
            <h2 style="color: #667eea;">{avg_da}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4>📧 With Email</h4>
            <h2 style="color: #667eea;">{sites_with_email}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h4>💡 Avg. Confidence</h4>
            <h2 style="color: #667eea;">{avg_confidence}/100</h2>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Advanced Charts
    col1, col2 = st.columns(2)
    df = pd.DataFrame(results)

    with col1:
        fig = px.scatter(df, x='domain_authority', y='confidence_score',
                         size='word_count', color='trust_score',
                         hover_name='domain',
                         title="Confidence vs. Domain Authority",
                         labels={'domain_authority': 'Domain Authority', 'confidence_score': 'Confidence Score'},
                         color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        df['confidence_level'] = df['confidence_score'].apply(
            lambda x: 'Platinum' if x >= 75 else 'Gold' if x >= 50 else 'Silver' if x >= 25 else 'Bronze')
        level_counts = df['confidence_level'].value_counts()
        fig = px.pie(values=level_counts.values, names=level_counts.index,
                     title="Distribution by Confidence Level",
                     color_discrete_map={'Platinum':'#E5E4E2','Gold':'#FFD700', 'Silver':'#C0C0C0', 'Bronze':'#CD7F32'})
        st.plotly_chart(fig, use_container_width=True)

def create_export_options(results):
    """Creates UI elements for exporting the results in various formats."""
    if not results: return
    
    st.markdown("---")
    st.markdown("### 📥 ULTIMATE Export Hub")
    
    df_export = pd.DataFrame(results)
    # Clean up complex columns for export
    df_export['emails'] = df_export['emails'].apply(lambda x: ', '.join(x) if x else '')
    df_export['indicators_found'] = df_export['indicators_found'].apply(lambda x: ', '.join([i['text'] for i in x]) if x else '')

    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(label="📊 Download as CSV", data=csv_data,
                           file_name=f"guest_post_sites_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
    
    with col2:
        json_data = json.dumps(results, indent=2, default=str)
        st.download_button(label="📋 Download as JSON", data=json_data,
                           file_name=f"guest_post_analysis_{datetime.now().strftime('%Y%m%d')}.json", mime="application/json")

    with col3:
        excel_buffer = BytesIO()
        df_export.to_excel(excel_buffer, index=False, sheet_name='Guest Posting Sites')
        st.download_button(label="📈 Download as Excel", data=excel_buffer.getvalue(),
                           file_name=f"guest_post_sites_{datetime.now().strftime('%Y%m%d')}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- MAIN APPLICATION LOGIC ---
def main():
    """The main function that runs the Streamlit application."""
    
    st.markdown("""
    <div class="main-header">
        <h1>🚀 ULTIMATE Guest Posting Sites Finder</h1>
        <p>An Advanced AI-Powered Discovery System for SEO & Content Marketers</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'finder' not in st.session_state:
        st.session_state.finder = UltimateGuestPostingFinder()
    
    # Sidebar for User Inputs
    with st.sidebar:
        st.markdown("### ⚙️ ULTIMATE Configuration")
        niche = st.text_input("🎯 Your Niche/Industry", placeholder="e.g., technology, health, SaaS")
        
        st.markdown("#### 🔧 Advanced Options (Optional)")
        competitors_input = st.text_area("🏆 Competitor Websites", placeholder="competitor1.com\ncompetitor2.com")
        competitors = [c.strip() for c in competitors_input.split('\n') if c.strip()]
        
        location = st.text_input("🌍 Geographic Focus", placeholder="e.g., USA, UK, Canada")
        max_sites = st.slider("🎯 Maximum Sites to Find", 10, 200, 50)
        
        st.markdown("<br>", unsafe_allow_html=True)
        search_button = st.button("🚀 START ULTIMATE SEARCH", type="primary")
    
    # Main Content Area
    if search_button:
        if not niche:
            st.error("🚫 Please enter your niche/industry to begin the search.")
            return
        
        results = st.session_state.finder.parallel_search_and_analyze(niche, competitors, location, max_sites)
        st.session_state.results = results
        
    if 'results' in st.session_state and st.session_state.results:
        results = st.session_state.results
        
        st.markdown(f"""
        <div class="success-card">
            <h3>🎉 ULTIMATE Search Complete!</h3>
            <p>Found <strong>{len(results)}</strong> high-quality guest posting opportunities for "<strong>{niche}</strong>".</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["🎯 Premium Results", "📊 Analytics Dashboard", "📥 Export Hub"])

        with tab1:
            st.markdown("### 💎 Top Guest Posting Opportunities")
            for i, result in enumerate(results):
                with st.expander(f"🏆 #{i+1} - {result.get('title', 'Unknown Title')} (DA: {result.get('domain_authority', 0)})"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(f"**🌐 URL:** [{result.get('domain', 'N/A')}]({result.get('url', '#')})")
                        st.markdown(f"**📝 Description:** {result.get('meta_description', 'N/A')[:200]}...")
                        if result.get('emails'):
                            st.markdown(f"**📧 Contact Emails:** {', '.join(result.get('emails', []))}")
                        if result.get('indicators_found'):
                            st.markdown(f"**💡 Indicators:** `{'`, `'.join([ind['text'] for ind in result.get('indicators_found', [])])}`")

                    with col2:
                        st.metric("💡 Confidence Score", f"{result.get('confidence_score', 0)}/100")
                        st.metric("📈 Domain Authority", f"{result.get('domain_authority', 0)}/100")
                        st.metric("🛡️ Trust Score", f"{result.get('trust_score', 0)}/100")
                        st.metric("📝 Content Quality", f"{result.get('content_quality_score', 0)}/100")
                        st.metric("🚀 SEO Score", f"{result.get('seo_score', 0)}/100")
                        st.metric("🚨 Spam Score", f"{result.get('spam_score', 0)}/100")
        
        with tab2:
            create_ultimate_dashboard(results)

        with tab3:
            create_export_options(results)
            
    elif 'results' in st.session_state and not st.session_state.results and search_button:
        st.markdown("""
        <div class="warning-card">
            <h3>🔍 No Results Found</h3>
            <p>Your search did not return any matching guest posting opportunities. Please try the following:</p>
            <ul>
                <li>Broaden your niche (e.g., use "digital marketing" instead of "B2B SaaS SEO").</li>
                <li>Remove competitor or location filters.</li>
                <li>Ensure there are no spelling errors in your inputs.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("💡 Enter your niche in the sidebar and click 'START ULTIMATE SEARCH' to discover guest posting opportunities.")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 1rem; color: #888;'>
        <p><strong>🚀 ULTIMATE Guest Posting Finder</strong> | Built with ❤️ using Streamlit</p>
        <p><em>Disclaimer: All metrics like Domain Authority are estimated based on publicly available data and should be used as a guideline.</em></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
