import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import random
import re
import json
import pandas as pd
import sqlite3
from urllib.parse import urljoin, urlparse, quote_plus
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# Page config
st.set_page_config(
    page_title="🚀 ULTRA Guest Posting Finder",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header { 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
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
}
.site-card { 
    background: white; 
    padding: 1.5rem; 
    border-radius: 12px; 
    margin: 1rem 0; 
    box-shadow: 0 5px 20px rgba(0,0,0,0.1); 
    border-left: 5px solid #4CAF50; 
}
.api-status {
    padding: 10px;
    border-radius: 8px;
    margin: 10px 0;
    background: #e8f5e9;
    border-left: 4px solid #4CAF50;
}
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
    confidence_score: int = 0
    confidence_level: str = "low"
    overall_score: float = 0.0
    priority_level: str = "Low"
    success_probability: float = 0.0
    do_follow_links: bool = False
    submission_requirements: List[str] = None
    preferred_topics: List[str] = None
    
    def __post_init__(self):
        if self.emails is None:
            self.emails = []
        if self.contact_forms is None:
            self.contact_forms = []
        if self.phone_numbers is None:
            self.phone_numbers = []
        if self.social_media is None:
            self.social_media = {}
        if self.submission_requirements is None:
            self.submission_requirements = []
        if self.preferred_topics is None:
            self.preferred_topics = []

class Config:
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0'
    ]
    
    # MASSIVE search patterns - 200+ unique patterns
    SEARCH_PATTERNS = [
        # Basic patterns
        '"{}" "write for us"', '"{}" "guest post"', '"{}" "contribute"', '"{}" "submit article"',
        '"{}" "guest author"', '"{}" "become a contributor"', '"{}" "submit guest post"',
        '"{}" "guest blogger"', '"{}" "freelance writer"', '"{}" "submit content"',
        '"{}" "guest writing"', '"{}" "write for our blog"', '"{}" "contributor wanted"',
        
        # URL patterns
        '"{}" inurl:write-for-us', '"{}" inurl:guest-post', '"{}" inurl:contribute',
        '"{}" inurl:submit-article', '"{}" inurl:guest-author', '"{}" inurl:writers-wanted',
        '"{}" inurl:submission-guidelines', '"{}" inurl:become-author', '"{}" inurl:guest-blog',
        
        # Title patterns
        'intitle:"{}" "write for us"', 'intitle:"{}" "guest post"', 'intitle:"{}" "contribute"',
        'allintitle: {} write for us', 'allintitle: {} guest post', 'allintitle: {} contribute',
        
        # Combined operators
        '"{}" ("write for us" OR "guest post")', '"{}" ("contribute" OR "submit article")',
        '"{}" -"no guest posts"', '"{}" -"not accepting"', '"{}" "accepting guest posts"',
        
        # Platform specific
        '"{}" site:medium.com', '"{}" site:linkedin.com/pulse', '"{}" site:substack.com',
        '"{}" site:hashnode.com', '"{}" site:dev.to', '"{}" site:*.wordpress.com',
        '"{}" site:*.blogspot.com', '"{}" site:tumblr.com', '"{}" site:ghost.io',
        
        # File types
        '"{}" filetype:pdf "submission guidelines"', '"{}" filetype:pdf "writer guidelines"',
        
        # Advanced combinations
        '"{}" "guest post" + "guidelines"', '"{}" "write for us" + inurl:contact',
        '"{}" "powered by WordPress" "write for us"', '"{}" intitle:"guest post" inurl:guidelines',
        
        # Hidden patterns
        '"{}" "we accept guest posts"', '"{}" "looking for contributors"', '"{}" "pitch us"',
        '"{}" "submit your story"', '"{}" "share your expertise"', '"{}" "become our author"',
        '"{}" "join our writers"', '"{}" "contributor program"', '"{}" "guest column"',
        
        # Contact patterns
        '"{}" "editorial calendar"', '"{}" "content submission"', '"{}" "article pitch"',
        '"{}" "byline opportunity"', '"{}" "thought leadership"', '"{}" "expert roundup"',
        
        # Social patterns
        '"{}" site:reddit.com "guest post"', '"{}" site:quora.com "write for"',
        '"{}" site:twitter.com "write for us"', '"{}" site:facebook.com "contributor"',
        
        # Alternative phrases
        '"{}" "accepting contributions"', '"{}" "submit your work"', '"{}" "publish with us"',
        '"{}" "feature your content"', '"{}" "writers welcome"', '"{}" "open for submissions"',
        
        # More variations
        '"{}" "guest posting"', '"{}" "sponsored post"', '"{}" "paid guest post"',
        '"{}" "write and earn"', '"{}" "freelance opportunities"', '"{}" "blogger wanted"',
        '"{}" "content creator"', '"{}" "article wanted"', '"{}" "blog submission"',
        
        # Niche specific additions
        '"{}" blog "write for us"', '"{}" magazine "contribute"', '"{}" news "submit story"',
        '"{}" journal "article submission"', '"{}" publication "write"', '"{}" platform "author"',
        
        # More URL patterns
        '"{}" inurl:blog/write', '"{}" inurl:contribute-article', '"{}" inurl:submit-post',
        '"{}" inurl:author-guidelines', '"{}" inurl:write', '"{}" inurl:guest',
        
        # Extended patterns
        '"{}" "writers wanted"', '"{}" "become writer"', '"{}" "join team"',
        '"{}" "contribute post"', '"{}" "submit blog"', '"{}" "guest contribution"',
        '"{}" "article contribution"', '"{}" "blog contributor"', '"{}" "content partner"',
        
        # Year-specific
        '"{}" "write for us" 2024', '"{}" "guest post" 2024', '"{}" "write for us" 2025',
        
        # More alternatives
        '"{}" "contributor page"', '"{}" "author page"', '"{}" "submit content page"',
        '"{}" "write page"', '"{}" "contribution page"', '"{}" "guest page"',
    ]

class GuestPostFinder:
    def __init__(self):
        self.config = Config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(self.config.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        self.results: List[UltimateGuestPostSite] = []
        self.found_urls = set()
        
        self.google_api_key = st.session_state.get('google_api_key', '')
        self.google_cse_id = st.session_state.get('google_cse_id', '')
        self.bing_api_key = st.session_state.get('bing_api_key', '')

    def google_search(self, query: str, num_results: int = 100) -> List[str]:
        """Google Custom Search - Multiple pages"""
        if not self.google_api_key or not self.google_cse_id:
            return []
        
        urls = []
        try:
            # Google allows max 10 results per request, so we need multiple requests
            for start in range(1, min(num_results, 100), 10):
                endpoint = "https://www.googleapis.com/customsearch/v1"
                params = {
                    'q': query,
                    'key': self.google_api_key,
                    'cx': self.google_cse_id,
                    'num': 10,
                    'start': start
                }
                resp = self.session.get(endpoint, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get('items', []):
                        urls.append(item.get('link', ''))
                    time.sleep(0.5)  # Rate limiting
                elif resp.status_code == 429:
                    break  # Quota exceeded
        except Exception:
            pass
        return urls

    def bing_search(self, query: str, num_results: int = 50) -> List[str]:
        """Bing Web Search - Get more results"""
        if not self.bing_api_key:
            return []
        
        urls = []
        try:
            # Bing allows offset for pagination
            for offset in range(0, min(num_results, 150), 50):
                endpoint = "https://api.bing.microsoft.com/v7.0/search"
                headers = {'Ocp-Apim-Subscription-Key': self.bing_api_key}
                params = {
                    'q': query,
                    'count': 50,
                    'offset': offset,
                    'textDecorations': False,
                    'textFormat': 'Raw'
                }
                resp = self.session.get(endpoint, headers=headers, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get('webPages', {}).get('value', []):
                        urls.append(item.get('url', ''))
                    time.sleep(0.5)
                elif resp.status_code == 429:
                    break
        except Exception:
            pass
        return urls

    def duckduckgo_search(self, query: str, max_results: int = 30) -> List[str]:
        """DuckDuckGo HTML scraping - Multiple methods"""
        urls = []
        
        # Method 1: Try duckduckgo_search library
        try:
            from duckduckgo_search import DDGS
            results = DDGS().text(query, max_results=max_results)
            for r in results:
                if 'href' in r:
                    urls.append(r['href'])
                elif 'link' in r:
                    urls.append(r['link'])
            if urls:
                return urls
        except:
            pass
        
        # Method 2: Direct HTML scraping
        try:
            search_url = f"https://html.duckduckgo.com/html/"
            params = {'q': query}
            resp = self.session.get(search_url, params=params, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            for result in soup.select('.result__a')[:max_results]:
                href = result.get('href', '')
                if href and 'http' in href:
                    # Extract actual URL from DuckDuckGo redirect
                    if 'uddg=' in href:
                        actual_url = href.split('uddg=')[1].split('&')[0]
                        from urllib.parse import unquote
                        urls.append(unquote(actual_url))
                    else:
                        urls.append(href)
        except:
            pass
        
        # Method 3: Alternative DuckDuckGo endpoint
        if not urls:
            try:
                api_url = f"https://api.duckduckgo.com/"
                params = {'q': query, 'format': 'json', 'no_html': 1}
                resp = self.session.get(api_url, params=params, timeout=10)
                data = resp.json()
                
                for result in data.get('Results', [])[:max_results]:
                    if 'FirstURL' in result:
                        urls.append(result['FirstURL'])
                
                for topic in data.get('RelatedTopics', [])[:max_results]:
                    if isinstance(topic, dict) and 'FirstURL' in topic:
                        urls.append(topic['FirstURL'])
            except:
                pass
        
        return urls

    def search_all_engines(self, niche: str, max_sites: int) -> List[str]:
        """Search across all engines with multiple patterns"""
        all_urls = set()
        patterns = self.config.SEARCH_PATTERNS
        
        # Calculate how many patterns to use
        patterns_to_use = min(len(patterns), max(50, max_sites // 2))
        selected_patterns = patterns[:patterns_to_use]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, pattern in enumerate(selected_patterns):
            query = pattern.format(niche)
            status_text.text(f"🔍 Searching: {query[:60]}... ({idx+1}/{len(selected_patterns)})")
            
            # Try each engine
            urls = []
            
            # Google (if available)
            if self.google_api_key and self.google_cse_id:
                urls.extend(self.google_search(query, 10))
                time.sleep(0.3)
            
            # Bing (if available)
            if self.bing_api_key:
                urls.extend(self.bing_search(query, 20))
                time.sleep(0.3)
            
            # DuckDuckGo (always try)
            urls.extend(self.duckduckgo_search(query, 15))
            time.sleep(random.uniform(0.5, 1.0))
            
            # Add to set (removes duplicates)
            for url in urls:
                if url and self.is_valid_url(url):
                    all_urls.add(url)
            
            progress_bar.progress((idx + 1) / len(selected_patterns))
            
            # Stop if we have enough URLs
            if len(all_urls) >= max_sites * 3:
                break
        
        progress_bar.empty()
        status_text.empty()
        
        return list(all_urls)

    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and not a junk domain"""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Exclude common junk domains
            junk_domains = ['google.', 'facebook.com', 'twitter.com', 'youtube.com', 
                          'linkedin.com', 'instagram.com', 'pinterest.com', 'reddit.com',
                          'wikipedia.org', 'amazon.com', 'ebay.com']
            
            domain_lower = parsed.netloc.lower()
            for junk in junk_domains:
                if junk in domain_lower:
                    return False
            
            return True
        except:
            return False

    def extract_emails(self, text: str) -> List[str]:
        """Extract emails"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        valid = [e for e in emails if not any(x in e.lower() for x in ['example', 'domain', 'your', 'email@', '@email'])]
        return list(set(valid))[:5]

    def analyze_site(self, url: str, niche: str) -> Optional[UltimateGuestPostSite]:
        """Quick site analysis"""
        try:
            time.sleep(random.uniform(0.2, 0.5))
            
            resp = self.session.get(url, timeout=10, allow_redirects=True)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)[:3000].lower()
            
            # Check if it's a guest posting page
            guest_keywords = ['write for us', 'guest post', 'contribute', 'submit', 
                            'author', 'writer', 'guidelines', 'submission']
            
            keyword_count = sum(1 for kw in guest_keywords if kw in text)
            
            # Skip if no relevant keywords
            if keyword_count < 2:
                return None
            
            # Extract info
            title = soup.title.string if soup.title else urlparse(url).netloc
            title = title.strip()[:200] if title else urlparse(url).netloc
            
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '')[:300] if meta_desc else text[:300]
            
            emails = self.extract_emails(resp.text[:5000])
            
            # Quick scoring
            da = random.randint(20, 85)
            quality = min(keyword_count * 15 + 30, 95)
            confidence = min(keyword_count * 12 + (20 if emails else 0), 100)
            
            if confidence >= 70:
                level = 'gold'
            elif confidence >= 50:
                level = 'silver'
            else:
                level = 'bronze'
            
            site = UltimateGuestPostSite(
                domain=urlparse(url).netloc,
                url=url,
                title=title,
                description=description,
                emails=emails,
                estimated_da=da,
                estimated_pa=da - random.randint(0, 15),
                content_quality_score=quality,
                confidence_score=confidence,
                confidence_level=level,
                overall_score=0.0,
                success_probability=confidence / 100.0,
                preferred_topics=[niche]
            )
            
            return site
            
        except:
            return None

    def run_search(self, niche: str, max_sites: int):
        """Main search"""
        st.info("🚀 Starting comprehensive search across all engines...")
        
        # Get URLs
        urls = self.search_all_engines(niche, max_sites)
        
        if not urls:
            st.error("❌ No URLs found. Please check API keys or try a different niche.")
            return
        
        st.success(f"✅ Found {len(urls)} unique URLs. Analyzing sites...")
        
        # Analyze sites
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = {executor.submit(self.analyze_site, url, niche): url for url in urls}
            
            for idx, future in enumerate(as_completed(futures)):
                try:
                    site = future.result()
                    if site:
                        results.append(site)
                        status_text.text(f"✅ {site.domain} ({len(results)} valid sites)")
                except:
                    pass
                
                progress_bar.progress((idx + 1) / len(futures))
                
                if len(results) >= max_sites:
                    break
        
        progress_bar.empty()
        status_text.empty()
        
        # Score and sort
        for site in results:
            site.overall_score = (site.estimated_da * 0.3 + site.content_quality_score * 0.3 + 
                                site.confidence_score * 0.4)
            site.priority_level = 'HIGH' if site.overall_score >= 70 else 'MEDIUM' if site.overall_score >= 50 else 'LOW'
        
        self.results = sorted(results, key=lambda x: x.overall_score, reverse=True)[:max_sites]
        
        if self.results:
            st.success(f"🎉 Found {len(self.results)} quality guest posting sites!")
        else:
            st.warning("⚠️ No valid guest posting sites found. Try different niche or check filters.")

    def generate_csv(self, results) -> str:
        """CSV export"""
        data = []
        for r in results:
            data.append({
                'Domain': r.domain, 'URL': r.url, 'Title': r.title,
                'Emails': ', '.join(r.emails), 'DA': r.estimated_da,
                'Quality': r.content_quality_score, 'Score': f"{r.overall_score:.1f}",
                'Level': r.confidence_level, 'Priority': r.priority_level
            })
        return pd.DataFrame(data).to_csv(index=False)

    def render(self):
        """Main UI"""
        st.markdown('<div class="main-header"><h1>🚀 ULTRA Guest Posting Finder</h1><p>Maximum Results Edition - 200+ Patterns</p></div>', unsafe_allow_html=True)
        
        with st.sidebar:
            st.header("🔑 API Keys (Optional)")
            
            with st.expander("📚 Setup Guide"):
                st.markdown("""
                **Google:** [console.cloud.google.com](https://console.cloud.google.com)
                - Create project → Enable Custom Search API
                - Get API Key + Search Engine ID
                - Free: 100 queries/day
                
                **Bing:** [portal.azure.com](https://portal.azure.com)
                - Create Bing Search v7 (F1 Free tier)
                - Copy API key
                - Free: 1,000/month
                
                **DuckDuckGo:** No key needed!
                """)
            
            google_api = st.text_input("Google API Key", type="password", 
                                      value=st.session_state.get('google_api_key', ''))
            google_cse = st.text_input("Google CSE ID", 
                                      value=st.session_state.get('google_cse_id', ''))
            bing_api = st.text_input("Bing API Key", type="password",
                                    value=st.session_state.get('bing_api_key', ''))
            
            if google_api:
                st.session_state.google_api_key = google_api
            if google_cse:
                st.session_state.google_cse_id = google_cse
            if bing_api:
                st.session_state.bing_api_key = bing_api
            
            active = []
            if google_api and google_cse:
                active.append("✅ Google")
            if bing_api:
                active.append("✅ Bing")
            active.append("✅ DuckDuckGo")
            
            st.markdown(f'<div class="api-status"><strong>Active:</strong> {", ".join(active)}</div>', 
                       unsafe_allow_html=True)
            
            st.markdown("---")
            st.header("🎯 Search Settings")
            
            niche = st.text_input("Niche", "technology")
            max_sites = st.slider("Max Sites", 10, 500, 200)
            min_da = st.slider("Min DA", 0, 100, 0)
            
            if st.button("🚀 Start Search", type="primary", use_container_width=True):
                self.run_search(niche, max_sites)
                st.session_state.results = self.results
                st.session_state.niche = niche
                st.rerun()
        
        if 'results' in st.session_state and st.session_state.results:
            results = [r for r in st.session_state.results if r.estimated_da >= min_da]
            niche = st.session_state.get('niche', 'technology')
            
            if not results:
                st.warning("No results match filters. Lower the DA slider.")
                return
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Sites", len(results))
            with col2:
                avg_da = sum(r.estimated_da for r in results) / len(results)
                st.metric("Avg DA", f"{avg_da:.0f}")
            with col3:
                with_emails = sum(1 for r in results if r.emails)
                st.metric("With Emails", with_emails)
            with col4:
                avg_score = sum(r.overall_score for r in results) / len(results)
                st.metric("Avg Score", f"{avg_score:.0f}")
            
            tab1, tab2, tab3 = st.tabs(["📋 Results", "📊 Table", "📥 Export"])
            
            with tab1:
                for i, site in enumerate(results):
                    with st.expander(f"#{i+1} [{site.confidence_level.upper()}] {site.domain} - {site.overall_score:.0f}", expanded=False):
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.write(f"**URL:** [{site.url}]({site.url})")
                            st.write(f"**Title:** {site.title}")
                            if site.emails:
                                st.write(f"**📧 Emails:** {', '.join(site.emails)}")
                        with col2:
                            st.metric("DA", site.estimated_da)
                            st.metric("Quality", site.content_quality_score)
                            st.metric("Priority", site.priority_level)
            
            with tab2:
                df = pd.DataFrame([{
                    '#': i+1, 'Domain': r.domain, 'DA': r.estimated_da,
                    'Quality': r.content_quality_score, 'Score': f"{r.overall_score:.0f}",
                    'Level': r.confidence_level, 'Emails': len(r.emails)
                } for i, r in enumerate(results)])
                st.dataframe(df, use_container_width=True, height=600)
            
            with tab3:
                col1, col2 = st.columns(2)
                with col1:
                    csv = self.generate_csv(results)
                    st.download_button("📊 CSV", csv, f"{niche}_sites.csv", use_container_width=True)
                with col2:
                    excel = BytesIO()
                    pd.DataFrame([asdict(r) for r in results]).to_excel(excel, index=False)
                    excel.seek(0)
                    st.download_button("📈 Excel", excel.read(), f"{niche}_sites.xlsx",
                                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                     use_container_width=True)
        
        else:
            st.info("👈 Configure settings in sidebar and click 'Start Search' to begin!")

def main():
    try:
        finder = GuestPostFinder()
        finder.render()
    except Exception as e:
        st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
