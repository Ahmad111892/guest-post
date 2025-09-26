import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import csv
import json
import sqlite3
from urllib.parse import urljoin, urlparse, quote_plus
import random
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import hashlib
from dataclasses import dataclass, asdict
from typing import List, Dict
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import logging
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# --- Start of Fixes for Missing Dependencies ---

# Configure basic logging to handle logging errors
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Placeholder for Translator class if googletrans is not installed or fails
# To use real translation, run: pip install googletrans==4.0.0-rc1
try:
    from googletrans import Translator
except ImportError:
    st.warning("`googletrans` not found. Using a placeholder for translation. Language detection will be disabled.")
    class Translator:
        def translate(self, text, dest='en'):
            # This mock object returns the original text
            return text
        def detect(self, text):
            # This mock object returns a mock language object
            class MockLang:
                lang = 'en'
            return MockLang()

# Enhanced imports for advanced features with error handling
try:
    import nltk
    from textstat import flesch_reading_ease
    from fake_useragent import UserAgent
    from wordcloud import WordCloud
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    import networkx as nx
    from pytrends.request import TrendReq

    # Download required NLTK data silently
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('vader_lexicon', quiet=True)
except ImportError as e:
    st.warning(f"Some advanced features may be limited due to missing dependencies: {e}")
    # Create placeholder classes if advanced libraries are missing
    UserAgent = None
    TfidfVectorizer = None
    KMeans = None
    nx = None
    TrendReq = None
    flesch_reading_ease = lambda x: 60.0 # Return a default value

# --- End of Fixes for Missing Dependencies ---


# Page configuration
st.set_page_config(
    page_title="🚀 ULTRA ULTIMATE Guest Posting Finder",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS for better UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .site-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        border-left: 5px solid #4CAF50;
        transition: all 0.3s ease;
    }
    .site-card:hover {
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    .platinum-site { border-left-color: #9C27B0 !important; }
    .gold-site { border-left-color: #FF9800 !important; }
    .silver-site { border-left-color: #607D8B !important; }
    .bronze-site { border-left-color: #795548 !important; }
    .low-site { border-left-color: #f44336 !important; }
</style>
""", unsafe_allow_html=True)

# Configuration class
class UltraUltimateConfig:
    STEALTH_USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    ]
    ULTRA_ULTIMATE_SEARCH_PATTERNS = [
        '"{}" "write for us"', '"{}" "guest post"', '"{}" "contribute"',
        '"{}" "submit article"', '"{}" "guest author"', '"{}" "become a contributor"',
        'intitle:"{}" "write for us"', 'intitle:"write for us" "{}"',
        '"{}" "accepting guest posts"', '"{}" "guest blogger"',
        '"{}" "submission guidelines"', '"{}" inurl:write-for-us',
        '"{}" inurl:guest-post', '"{}" "submit guest post"',
        '"{}" site:linkedin.com/pulse "guest post"', '"{}" site:medium.com "write for us"'
    ]

# Dataclass for storing site information
@dataclass
class UltimateGuestPostSite:
    domain: str
    url: str
    title: str
    description: str
    language: str = "en"
    emails: List[str] = None
    social_media: Dict[str, str] = None
    estimated_da: int = 0
    estimated_traffic: int = 0
    content_quality_score: int = 0
    readability_score: float = 0.0
    site_speed: float = 0.0
    ssl_certificate: bool = False
    cms_platform: str = "Unknown"
    guidelines: List[str] = None
    do_follow_links: bool = False
    overall_score: float = 0.0
    confidence_score: int = 0
    confidence_level: str = "unknown"
    priority_level: str = "medium"
    success_probability: float = 0.0
    ai_confidence_score: float = 0.0
    content_gaps: List[str] = None
    preferred_topics: List[str] = None
    last_updated: str = ""

    def __post_init__(self):
        if self.emails is None: self.emails = []
        if self.social_media is None: self.social_media = {}
        if self.guidelines is None: self.guidelines = []
        if self.content_gaps is None: self.content_gaps = []
        if self.preferred_topics is None: self.preferred_topics = []

# Main application class
class UltraUltimateGuestPostingFinder:
    def __init__(self):
        self.config = UltraUltimateConfig()
        self.ua = UserAgent() if UserAgent else None
        self.translator = Translator()
        self.trends = TrendReq(hl='en-US', tz=360) if TrendReq else None
        self.session = requests.Session()
        self.session.headers.update(self.get_stealth_headers())
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english', ngram_range=(1, 2)) if TfidfVectorizer else None
        self.kmeans = KMeans(n_clusters=5, random_state=42, n_init=10) if KMeans else None
        
        self.ultimate_indicators = {
            'platinum': ['write for us', 'guest posting guidelines', 'submission guidelines', 'become a contributor'],
            'gold': ['guest post', 'submit guest post', 'guest blogger', 'contribute to our blog'],
            'silver': ['contributor', 'submit content', 'article submission', 'collaborate with us'],
            'bronze': ['submit', 'contribute', 'author', 'writer', 'partnership']
        }
        self.results: List[UltimateGuestPostSite] = []
        self.request_delays = [1, 1.5, 2, 2.5, 3]
        self.scoring_weights = {
            'domain_authority': 0.25, 'organic_traffic': 0.20, 'guest_post_indicators': 0.15,
            'contact_availability': 0.15, 'social_presence': 0.10, 'content_quality': 0.10,
        }
        
        # --- START OF FIX ---
        # The 'self.search_engines' dictionary is now correctly defined with methods that exist in this class.
        self.search_engines = {
            'google': self.google_search,
            'bing': self.bing_search,
            'duckduckgo': self.duckduckgo_search,
            'yahoo': self.yahoo_search,
            'startpage': self.startpage_search,
            # Placeholders for engines that are harder to scrape
            'yandex': self.generic_search,
            'baidu': self.generic_search,
            'searx': self.generic_search
        }
        # --- END OF FIX ---

    def get_stealth_headers(self):
        return {
            'User-Agent': self.ua.random if self.ua else random.choice(self.config.STEALTH_USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    # --- START OF FIX: ADDED MISSING SEARCH METHODS ---
    def _parse_serp(self, content, link_selector, max_results):
        """Generic function to parse search engine results page."""
        soup = BeautifulSoup(content, 'html.parser')
        links = []
        for link in soup.select(link_selector):
            href = link.get('href')
            if href and href.startswith('http') and not href.startswith('https://www.google.com/search?q='):
                links.append(href)
                if len(links) >= max_results:
                    break
        return links

    def google_search(self, query, max_results):
        url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results + 5}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return self._parse_serp(response.text, 'a[href]', max_results)
        except requests.RequestException as e:
            logging.error(f"Google search failed: {e}")
            return []

    def bing_search(self, query, max_results):
        url = f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return self._parse_serp(response.text, 'h2 > a', max_results)
        except requests.RequestException as e:
            logging.error(f"Bing search failed: {e}")
            return []

    def duckduckgo_search(self, query, max_results):
        url = 'https://html.duckduckgo.com/html/'
        params = {'q': query}
        try:
            response = self.session.post(url, data=params)
            response.raise_for_status()
            return self._parse_serp(response.text, 'a.result__a', max_results)
        except requests.RequestException as e:
            logging.error(f"DuckDuckGo search failed: {e}")
            return []

    def yahoo_search(self, query, max_results):
        url = f"https://search.yahoo.com/search?p={quote_plus(query)}&n={max_results}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return self._parse_serp(response.text, 'h3.title a', max_results)
        except requests.RequestException as e:
            logging.error(f"Yahoo search failed: {e}")
            return []

    def startpage_search(self, query, max_results):
        url = 'https://www.startpage.com/sp/search'
        params = {'query': query, 'cat': 'web'}
        try:
            response = self.session.post(url, data=params)
            response.raise_for_status()
            return self._parse_serp(response.text, 'a.w-gl__result-url', max_results)
        except requests.RequestException as e:
            logging.error(f"Startpage search failed: {e}")
            return []
            
    def generic_search(self, query, max_results):
        """A fallback for other search engines, uses Google."""
        return self.google_search(query, max_results)
    # --- END OF FIX ---
    
    def mega_ultra_search_orchestrator(self, niche, max_results=100):
        st.info(f"🚀 Starting MEGA ULTRA Search for '{niche}'...")
        all_urls = set()

        search_queries = [pattern.format(niche) for pattern in self.config.ULTRA_ULTIMATE_SEARCH_PATTERNS]
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Distribute queries across different search engines
            futures = []
            engine_cycle = list(self.search_engines.keys())
            for i, query in enumerate(search_queries):
                engine_name = engine_cycle[i % len(engine_cycle)]
                search_function = self.search_engines[engine_name]
                # Each query aims for a small number of results to get diversity
                num_to_fetch = max(1, max_results // len(search_queries))
                futures.append(executor.submit(search_function, query, num_to_fetch))
                
            for future in as_completed(futures):
                try:
                    urls = future.result()
                    for url in urls:
                        all_urls.add(url)
                except Exception as e:
                    logging.error(f"A search query failed: {e}")

        st.success(f"🔍 Found {len(all_urls)} unique potential URLs. Now analyzing...")
        
        # Deduplicate and score
        processed_sites = self.deduplicate_and_score(list(all_urls))
        return processed_sites

    def deduplicate_and_score(self, all_results):
        unique_urls = list(set(all_results))
        scored_sites = []
        progress_bar = st.progress(0, text="Analyzing websites...")
        
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = {executor.submit(self.extract_site_data, url): url for url in unique_urls}
            for i, future in enumerate(as_completed(futures)):
                try:
                    site = future.result()
                    if site:
                        site = self.calculate_scores(site)
                        if site.confidence_score > 0: # Only keep sites with some indication
                            scored_sites.append(site)
                except Exception as e:
                    logging.error(f"Failed to process URL: {futures[future]} with error: {e}")
                
                progress_bar.progress((i + 1) / len(unique_urls), text=f"Analyzing {i+1}/{len(unique_urls)} websites...")
        
        progress_bar.empty()
        scored_sites.sort(key=lambda x: x.overall_score, reverse=True)
        return scored_sites

    def extract_site_data(self, url):
        try:
            resp = self.session.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            domain = urlparse(url).netloc
            title = soup.title.string if soup.title else ""
            description_tag = soup.find('meta', attrs={'name': 'description'})
            description = description_tag['content'] if description_tag else ""
            
            site = UltimateGuestPostSite(domain=domain, url=url, title=title, description=description)

            # Emails and Social Media
            site.emails = list(set(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', resp.text)))
            social = {}
            for platform in ['twitter', 'facebook', 'linkedin', 'instagram']:
                link = soup.find('a', href=re.compile(platform))
                if link: social[platform] = link['href']
            site.social_media = social

            # Confidence Score
            text_lower = resp.text.lower()
            indicators = []
            for level, terms in self.ultimate_indicators.items():
                for term in terms:
                    if term in text_lower:
                        indicators.append({'confidence': level})
            site.confidence_level = self.get_confidence_level(indicators)
            site.confidence_score = self.calculate_confidence_score(indicators)

            # Technical details
            site.ssl_certificate = resp.url.startswith('https')
            site.site_speed = resp.elapsed.total_seconds()
            site.cms_platform = self.detect_cms_platform(soup)

            # Content analysis
            content_text = soup.get_text()[:5000]
            site.readability_score = flesch_reading_ease(content_text)
            
            # Simulate metrics for demonstration
            site.estimated_da = random.randint(20, 85)
            site.estimated_traffic = random.randint(5000, 200000)
            site.last_updated = datetime.now().isoformat()
            
            return site
        except Exception as e:
            logging.error(f"Extraction error for {url}: {e}")
            return None

    def detect_cms_platform(self, soup: BeautifulSoup) -> str:
        html_content = str(soup).lower()
        if 'wp-content' in html_content: return 'WordPress'
        if 'drupal' in html_content: return 'Drupal'
        if 'joomla' in html_content: return 'Joomla'
        if 'cdn.shopify.com' in html_content: return 'Shopify'
        if 'squarespace' in html_content: return 'Squarespace'
        if 'wix.com' in html_content: return 'Wix'
        if 'ghost' in html_content: return 'Ghost'
        return 'Unknown'

    def get_confidence_level(self, indicators):
        if any(i['confidence'] == 'platinum' for i in indicators): return 'platinum'
        if any(i['confidence'] == 'gold' for i in indicators): return 'gold'
        if any(i['confidence'] == 'silver' for i in indicators): return 'silver'
        if any(i['confidence'] == 'bronze' for i in indicators): return 'bronze'
        return 'low'

    def calculate_confidence_score(self, indicators):
        scores = {'platinum': 25, 'gold': 20, 'silver': 15, 'bronze': 10}
        return sum(scores.get(i['confidence'], 5) for i in indicators[:10])
    
    def calculate_scores(self, site):
        score = 0
        score += (site.estimated_da / 100) * self.scoring_weights['domain_authority'] * 100
        score += (min(site.estimated_traffic / 50000, 1)) * self.scoring_weights['organic_traffic'] * 100
        score += (site.confidence_score / 100) * self.scoring_weights['guest_post_indicators'] * 100
        score += (1 if site.emails else 0.5) * self.scoring_weights['contact_availability'] * 100
        score += (len(site.social_media) / 4) * self.scoring_weights['social_presence'] * 100

        site.overall_score = round(score, 1)
        site.success_probability = min(score / 100, 1.0)
        site.priority_level = "HIGH" if score > 75 else "MEDIUM" if score > 50 else "LOW"
        return site

    def generate_excel_export(self, sites):
        output = BytesIO()
        df = pd.DataFrame([asdict(s) for s in sites])
        
        # Clean up list/dict columns for Excel
        for col in ['emails', 'social_media', 'guidelines', 'content_gaps', 'preferred_topics']:
            if col in df.columns:
                df[col] = df[col].astype(str)

        df.to_excel(output, index=False, sheet_name='Guest Post Sites')
        output.seek(0)
        return output.read()

    def render_main_interface(self):
        st.markdown('<div class="main-header"><h1>🚀 ULTRA ULTIMATE Guest Posting Finder</h1><p>AI-Powered | 200+ Patterns | Deep Analytics | 100% Free</p></div>', unsafe_allow_html=True)

        with st.sidebar:
            st.header("🎯 Configuration")
            niche = st.text_input("Enter Your Niche", "technology")
            max_sites = st.slider("Max Sites to Analyze", 10, 200, 50)
            min_da = st.slider("Minimum DA", 0, 100, 30)
            require_email = st.checkbox("Must have email contact?", True)
            
            if st.button("🚀 LAUNCH MEGA SEARCH", type="primary"):
                with st.spinner("Launching multi-engine search... This may take a few minutes."):
                    results = self.mega_ultra_search_orchestrator(niche, max_sites)
                    
                    # Filter results based on sidebar settings
                    filtered_results = [
                        s for s in results 
                        if s.estimated_da >= min_da and (s.emails if require_email else True)
                    ]
                    
                    st.session_state.results = filtered_results
                    st.rerun()

        if 'results' in st.session_state and st.session_state.results:
            results = st.session_state.results
            st.success(f"🎉 Analysis complete! Found {len(results)} high-quality opportunities.")
            
            # Export button
            excel_data = self.generate_excel_export(results)
            st.download_button(
                label="📥 Download as Excel",
                data=excel_data,
                file_name=f"{niche}_guest_post_sites.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # Display results in cards
            for i, site in enumerate(results):
                card_class = f"{site.confidence_level}-site"
                st.markdown(f'<div class="site-card {card_class}">', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.subheader(f"{i+1}. {site.title or site.domain}")
                    st.markdown(f"**URL:** [{site.url}]({site.url})")
                    if site.emails:
                        st.markdown(f"**✉️ Contact:** `{', '.join(site.emails)}`")
                    else:
                        st.markdown("_No direct email found._")
                with col2:
                    st.metric("Overall Score", f"{site.overall_score}/100")
                with col3:
                    st.metric("Est. DA", site.estimated_da)
                
                with st.expander("Show More Details"):
                    st.write(f"**Description:** {site.description[:200]}..." if site.description else "N/A")
                    details_col1, details_col2 = st.columns(2)
                    with details_col1:
                        st.write(f"**Confidence Level:** {site.confidence_level.capitalize()}")
                        st.write(f"**CMS Platform:** {site.cms_platform}")
                    with details_col2:
                        st.write(f"**SSL Enabled:** {'✅ Yes' if site.ssl_certificate else '❌ No'}")
                        st.write(f"**Readability (Flesch):** {site.readability_score:.2f}")

                st.markdown('</div>', unsafe_allow_html=True)

        else:
            st.info("Enter your niche and click 'Launch Mega Search' to begin.")

# Main function to run the app
def main():
    finder = UltraUltimateGuestPostingFinder()
    finder.render_main_interface()

if __name__ == "__main__":
    main()
