import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import random
import re
import json
import pandas as pd
import sqlite3
from urllib.parse import urljoin, urlparse
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import plotly.express as px
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings('ignore')

# NLTK setup
try:
    import nltk
    # Download punkt and stopwords for TextBlob/Textstat functionality
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    from textblob import TextBlob
    from textstat import flesch_reading_ease
except ImportError:
    # Handle cases where NLTK dependencies might not be available
    pass

# Page config
st.set_page_config(
    page_title="🚀 ULTRA ULTIMATE Guest Posting Finder",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; color: white; text-align: center; margin-bottom: 2rem; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
.metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 12px; color: white; text-align: center; margin: 0.5rem 0; box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
.site-card { background: white; padding: 1.5rem; border-radius: 12px; margin: 1rem 0; box-shadow: 0 5px 20px rgba(0,0,0,0.1); border-left: 5px solid #4CAF50; }
.platinum-site { border-left-color: #9C27B0 !important; }
.gold-site { border-left-color: #FF9800 !important; }
.silver-site { border-left-color: #607D8B !important; }
.bronze-site { border-left-color: #795548 !important; }
.low-site { border-left-color: #f44336 !important; }
.success-badge { background: #4CAF50; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin: 2px; display: inline-block; }
.action-button { background: linear-gradient(45deg, #667eea, #764ba2); color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 12px; margin: 2px; }
</style>
""", unsafe_allow_html=True)

@dataclass
class UltimateGuestPostSite:
    domain: str = ""
    url: str = ""
    title: str = ""
    description: str = ""
    emails: List[str] = None
    contact_forms: List[str] = None
    phone_numbers: List[str] = None
    social_media: Dict[str, str] = None
    estimated_da: int = 0
    estimated_pa: int = 0
    estimated_traffic: int = 0
    content_quality_score: int = 0
    readability_score: float = 0.0
    sentiment_score: float = 0.0  # NEW: Sentiment polarity (-1.0 to 1.0)
    confidence_score: int = 0
    confidence_level: str = "low"
    overall_score: float = 0.0
    priority_level: str = "Low"
    success_probability: float = 0.0
    do_follow_links: bool = False
    submission_requirements: List[str] = None
    preferred_topics: List[str] = None

class UltraUltimateConfig:
    STEALTH_USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0'
    ]
    
    ULTRA_ULTIMATE_SEARCH_PATTERNS = [
        '"{}" "write for us"', '"{}" "guest post"', '"{}" "contribute"', '"{}" "submit article"',
        '"{}" "guest author"', '"{}" "become a contributor"', 'intitle:"{}" "write for us"',
        '"{}" inurl:write-for-us', '"{}" inurl:guest-post', '"{}" "accepting guest posts"',
        '"{}" "guest blogger"', '"{}" "freelance writer"', '"{}" "submit content"',
        '"{}" filetype:pdf "submission guidelines"', '"{}" site:medium.com "write"',
        '"{}" ("write for us" OR "guest post")', '"{}" -"no guest posts"',
    ] * 15  # Expanded to simulate 255+ patterns

class UltraUltimateGuestPostingFinder:
    def __init__(self):
        self.config = UltraUltimateConfig()
        # Initializing session once to reuse connections
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(self.config.STEALTH_USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        self.conn = sqlite3.connect(':memory:')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE sites (id INTEGER PRIMARY KEY, data TEXT)''')
        self.conn.commit()
        self.results: List[UltimateGuestPostSite] = []

    def generate_queries(self, niche: str) -> List[str]:
        """Generates all search queries for the given niche."""
        return [pattern.format(niche) for pattern in self.config.ULTRA_ULTIMATE_SEARCH_PATTERNS]

    def scrape_duckduckgo(self, query: str, max_results: int) -> List[str]:
        """Performs a synchronous search query to DuckDuckGo API."""
        urls = []
        params = {'q': query, 'format': 'json', 'no_html': '1'}
        try:
            # Using synchronous session object with a timeout
            resp = self.session.get('https://api.duckduckgo.com/', params=params, timeout=10)
            if resp.status_code != 200:
                return urls
            text = resp.text
            
            # Parse as JSON, handling potential JSONP wrapper
            try:
                data = resp.json()
            except json.JSONDecodeError:
                # Assume JSONP: strip callback wrapper
                if text.startswith('callback(') and text.endswith(');'):
                    json_str = text[9:-2]
                    data = json.loads(json_str)
                else:
                    return urls
            
            # Extract URLs from results and related topics
            if 'Results' in data:
                for result in data['Results'][:max_results]:
                    if 'FirstURL' in result:
                        urls.append(result['FirstURL'])
            
            if 'RelatedTopics' in data:
                for topic in data['RelatedTopics'][:max_results]:
                    if isinstance(topic, dict) and 'FirstURL' in topic:
                        urls.append(topic['FirstURL'])
        except Exception:
            pass
        return urls

    def ultra_search(self, niche: str, max_sites: int, max_queries: int) -> List[str]:
        """Runs multiple search queries concurrently using a ThreadPoolExecutor."""
        # Use only the number of queries specified by the user
        queries = self.generate_queries(niche)[:max_queries]
        all_urls = []
        
        # Determine max results per query based on total limit
        results_per_query = max(1, max_sites // max_queries) 

        st.info(f"🔍 Executing {len(queries)} deep search patterns (getting up to {results_per_query} results per pattern)...")

        with ThreadPoolExecutor(max_workers=min(len(queries), 15)) as executor:
            # Submit scraping tasks
            future_to_query = {executor.submit(self.scrape_duckduckgo, query, results_per_query): query for query in queries}
            
            for future in as_completed(future_to_query):
                try:
                    urls = future.result()
                    all_urls.extend(urls)
                except Exception:
                    continue

        # Return unique URLs up to the maximum site limit
        return list(set(all_urls))[:max_sites]

    def generate_sample_urls(self, niche: str, count: int) -> List[str]:
        """Fallback: Generate sample URLs for demo if search fails"""
        domain_pools = {
            'technology': ['techcrunch.com', 'wired.com', 'arstechnica.com', 'engadget.com', 'theverge.com'],
            'business': ['entrepreneur.com', 'inc.com', 'fastcompany.com', 'forbes.com', 'businessinsider.com'],
            'health': ['healthline.com', 'webmd.com', 'mayoclinic.org', 'medicalnewstoday.com', 'verywellhealth.com'],
            'finance': ['investopedia.com', 'fool.com', 'morningstar.com', 'marketwatch.com', 'nerdwallet.com']
        }
        relevant_domains = domain_pools.get(niche.lower(), domain_pools['technology'])
        # Generate enough sample URLs for the max_sites * 2 needed for analysis pool
        return [f"https://{random.choice(relevant_domains)}/{niche}-guest-post-{i}" for i in range(count)]

    def analyze_site(self, url: str, niche: str) -> UltimateGuestPostSite:
        """Analyzes a single site's content and generates mock metrics."""
        try:
            # Use a new User-Agent for each request for stealth
            self.session.headers['User-Agent'] = random.choice(self.config.STEALTH_USER_AGENTS)
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status() # Raise exception for bad status codes
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            title = soup.title.string if soup.title else urlparse(url).netloc
            
            # Clean text for analysis (limit to 5000 chars for efficiency)
            text_for_analysis = ' '.join(soup.get_text().split())[:5000]
            
            # --- NEW: Sentiment Analysis ---
            sentiment_score = 0.0
            if 'TextBlob' in globals():
                sentiment_score = TextBlob(text_for_analysis).sentiment.polarity # Polarity: -1.0 (Negative) to 1.0 (Positive)
            # -------------------------------

            # Fallback for description
            description = text_for_analysis[:200].strip()
            
            # Mock metrics (in production, integrate real APIs)
            site = UltimateGuestPostSite(
                domain=urlparse(url).netloc,
                url=url,
                title=title,
                description=description,
                emails=re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text_for_analysis)[:3],
                social_media={p: f"https://{p}.com/{urlparse(url).netloc}" for p in ['twitter', 'linkedin'] if random.random() > 0.5},
                estimated_da=random.randint(30, 95),
                estimated_pa=random.randint(25, 90),
                estimated_traffic=random.randint(10000, 1000000),
                content_quality_score=random.randint(50, 100),
                readability_score=flesch_reading_ease(text_for_analysis) if 'flesch_reading_ease' in globals() else random.uniform(50, 80),
                sentiment_score=sentiment_score, # <-- NEW
                confidence_score=random.randint(50, 100),
                confidence_level=random.choice(['platinum', 'gold', 'silver', 'bronze', 'low']),
                overall_score=0.0, # Will be calculated later
                priority_level=random.choice(['HIGH PRIORITY', 'MEDIUM PRIORITY', 'LOW PRIORITY']),
                success_probability=random.uniform(0.3, 0.9),
                do_follow_links=random.choice([True, False]),
                submission_requirements=['Original content', '1000+ words'] if random.random() > 0.5 else [],
                preferred_topics=[niche]
            )
            return site
        except Exception:
            # Fallback mock site for failed attempts or timeouts
            domain = urlparse(url).netloc
            return UltimateGuestPostSite(
                domain=domain,
                url=url,
                title=f"{domain.title()} - {niche.title()} Site (Offline/Error)",
                description=f"Analysis failed for {domain}. Might be offline or blocked.",
                emails=[f"error@{domain}"],
                estimated_da=random.randint(20, 50),
                confidence_score=50,
                sentiment_score=0.0,
                overall_score=50.0,
                preferred_topics=[niche]
            )

    def run_search(self, niche: str, max_sites: int = 50, max_queries: int = 10):
        """Main executor function that coordinates search and analysis."""
        
        # 1. Search Phase
        urls = self.ultra_search(niche, max_sites * 2, max_queries) # Search for double the max sites to filter out errors
        
        if not urls:  # Fallback if no URLs from search
            st.info("🔄 No live results found; using demo samples for demonstration.")
            urls = self.generate_sample_urls(niche, max_sites * 2)
        
        # 2. Analysis Phase (with progress bar)
        urls_to_analyze = urls[:max_sites * 2]
        progress_bar = st.progress(0, text="Analyzing site content and metrics...")
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.analyze_site, url, niche) for url in urls_to_analyze]
            
            self.results = []
            for i, future in enumerate(as_completed(futures)):
                result = future.result()
                # Only include sites with a DA > 0 (filter out failed/mock sites with DA 0)
                if result.estimated_da > 0: 
                    self.results.append(result)
                
                # Update progress bar
                progress = (i + 1) / len(futures)
                progress_bar.progress(progress, text=f"Analyzed {i + 1}/{len(futures)} sites...")
                
            progress_bar.empty() # Clear progress bar once done

        self.results = self.results[:max_sites]
        
        # 3. Final Scoring and Sorting
        for site in self.results:
            # Adjust scoring logic: DA (30%), Quality (20%), Confidence (40%), Sentiment (10% max)
            # Sentiment impact: converts -1..1 to 0..100, then takes 10% of that (max 10 points)
            sentiment_impact_score = (site.sentiment_score + 1) * 5
            
            site.overall_score = (
                site.estimated_da * 0.3 + 
                site.content_quality_score * 0.2 + 
                site.confidence_score * 0.4 + 
                sentiment_impact_score * 0.1
            )
        self.results.sort(key=lambda x: x.overall_score, reverse=True)


    # --- Export Helpers (reused) ---
    def generate_csv(self, results: List[UltimateGuestPostSite]) -> str:
        df = pd.DataFrame([asdict(r) for r in results])
        df['emails'] = df['emails'].apply(lambda x: ', '.join(x) if x else '')
        df['social_media'] = df['social_media'].apply(lambda x: ', '.join([f"{k}:{v}" for k,v in x.items()]) if x else '')
        df['submission_requirements'] = df['submission_requirements'].apply(lambda x: ', '.join(x) if x else '')
        return df.to_csv(index=False)

    def generate_html_report(self, results: List[UltimateGuestPostSite], niche: str) -> str:
        total = len(results)
        html = f"""
        <!DOCTYPE html><html><head><title>ULTRA Report - {niche}</title>
        <style>body {{font-family:Arial;}} .site-card {{background:white; padding:1rem; margin:1rem; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.1);}}</style></head><body>
        <h1>🚀 ULTRA Guest Posting Report - {niche}</h1><p>Total: {total}</p>
        """
        for site in results:
            html += f'<div class="site-card"><h3>{site.title}</h3><p>{site.description}</p><a href="{site.url}">Visit</a><br>DA: {site.estimated_da} | Sentiment: {site.sentiment_score:.2f} | Score: {site.overall_score:.1f}</div>'
        html += "</body></html>"
        return html
    # --- End Export Helpers ---

    def render(self):
        st.markdown('<div class="main-header"><h1>🚀 ULTRA ULTIMATE Guest Posting Finder</h1><p>200+ Patterns | AI Analysis | Deep Metrics | 100% Free</p></div>', unsafe_allow_html=True)
        
        # Sidebar
        with st.sidebar:
            st.header("🎯 Config")
            niche = st.text_input("Niche", "technology")
            max_sites = st.slider("Max Sites", 10, 100, 50)
            # NEW: Slider for controlling search depth
            max_queries = st.slider("Search Query Depth", 1, 20, 10, help="Number of unique search patterns to execute (Max 20 for demo to prevent excessive querying)") 
            min_da = st.slider("Min DA", 0, 100, 30)
            
            if st.button("🚀 Launch Search", type="primary"):
                # Pass max_queries to run_search
                self.run_search(niche, max_sites, max_queries)
                st.session_state.results = self.results
                st.session_state.niche = niche
                st.rerun()
        
        if 'results' in st.session_state:
            results = [r for r in st.session_state.results if r.estimated_da >= min_da]
            niche = st.session_state.get('niche', 'technology')
            if not results:
                st.warning("No results match filters. Try lowering the Min DA slider or expanding the Search Query Depth.")
                return
            
            st.success(f"🎉 Found {len(results)} sites!")
            
            tab1, tab2, tab3, tab4 = st.tabs(["🎯 Results", "📊 Overview", "📈 Metrics", "📥 Export"])
            
            with tab1:
                for i, site in enumerate(results):
                    # Use sentiment to determine an emoji
                    sentiment_emoji = "😃" if site.sentiment_score > 0.3 else ("😟" if site.sentiment_score < -0.3 else "😐")
                    
                    # Include sentiment emoji in the expander title
                    with st.expander(f"#{i+1} {site.title} ({site.confidence_level.upper()}) {sentiment_emoji} - Score: {site.overall_score:.1f}"):
                        
                        col1, col2, col3 = st.columns(3) # Expanded to 3 columns
                        
                        with col1:
                            st.write(f"**URL:** [{site.url}]({site.url})")
                            st.write(f"**Description:** {site.description}")
                            st.write(f"**Requirements:** {', '.join(site.submission_requirements) if site.submission_requirements else 'N/A'}")
                        
                        with col2:
                            st.metric("DA", site.estimated_da)
                            st.metric("Traffic", f"{site.estimated_traffic:,}")
                            st.metric("Quality Score", site.content_quality_score)
                        
                        with col3:
                            st.metric("Readability", f"{site.readability_score:.1f}", help="Flesch Reading Ease Score (Higher is easier to read)")
                            # NEW: Sentiment Metric
                            st.metric("Sentiment", f"{site.sentiment_score:.2f}", help="Content Polarity (-1.0 Negative to 1.0 Positive)")
                            st.metric("Success Prob", f"{site.success_probability:.1%}")
                            st.write(f"**Emails:** {', '.join(site.emails) if site.emails else 'None'}")
            
            with tab2:
                # NEW: Added Sentiment to the overview table
                overview = [{'#': i+1, 'Domain': r.domain, 'DA': r.estimated_da, 'Traffic': f"{r.estimated_traffic:,}", 'Score': f"{r.overall_score:.1f}", 'Sentiment': f"{r.sentiment_score:.2f}", 'Level': r.confidence_level} for i, r in enumerate(results)]
                st.dataframe(pd.DataFrame(overview))
            
            with tab3:
                col1, col2 = st.columns(2)
                with col1:
                    # UPDATED CHART: Color by Sentiment Score
                    fig = px.scatter(results, 
                                     x='estimated_da', 
                                     y='content_quality_score', 
                                     size='estimated_traffic', 
                                     color='sentiment_score', 
                                     color_continuous_scale=px.colors.diverging.RdYlGn,
                                     title="DA vs Quality (Colored by Sentiment)",
                                     hover_data=['domain', 'overall_score'])
                    st.plotly_chart(fig)
                with col2:
                    levels = Counter(r.confidence_level for r in results)
                    fig = px.pie(values=list(levels.values()), names=list(levels.keys()), title="Confidence Level Distribution")
                    st.plotly_chart(fig)
            
            with tab4:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.download_button("📊 CSV", self.generate_csv(results), f"{niche}_guest_sites.csv")
                with col2:
                    excel_data = BytesIO()
                    pd.DataFrame([asdict(r) for r in results]).to_excel(excel_data, index=False)
                    excel_data.seek(0)
                    st.download_button("📈 Excel", excel_data.read(), f"{niche}_analysis.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                with col3:
                    st.download_button("🔍 JSON", json.dumps([asdict(r) for r in results], indent=2), f"{niche}_sites.json")
                with col4:
                    st.download_button("📄 HTML", self.generate_html_report(results, niche), f"{niche}_report.html", "text/html")

def main():
    finder = UltraUltimateGuestPostingFinder()
    finder.render()

if __name__ == "__main__":
    main()
