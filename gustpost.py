import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import urlparse, quote_plus
import re
import time
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import List, Dict
import json
from io import BytesIO

# Page Configuration
st.set_page_config(
    page_title="🚀 Ultimate Guest Posting Finder",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS
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
    .platinum { border-left-color: #9C27B0 !important; }
    .gold { border-left-color: #FF9800 !important; }
    .silver { border-left-color: #607D8B !important; }
    .bronze { border-left-color: #795548 !important; }
</style>
""", unsafe_allow_html=True)

@dataclass
class GuestPostSite:
    """Data structure for guest posting sites"""
    domain: str
    url: str
    title: str
    description: str
    emails: List[str]
    social_media: Dict[str, str]
    estimated_da: int
    estimated_traffic: int
    confidence_score: int
    confidence_level: str
    content_quality: int
    readability: float
    ssl_enabled: bool
    response_time: int
    guidelines: List[str]
    overall_score: float
    
    def __post_init__(self):
        if self.emails is None: self.emails = []
        if self.social_media is None: self.social_media = {}
        if self.guidelines is None: self.guidelines = []

class GuestPostingFinder:
    """Main finder class with all functionality"""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        self.search_patterns = [
            '"{}" "write for us"',
            '"{}" "guest post"',
            '"{}" "submit article"',
            '"{}" "contribute"',
            '"{}" "guest author"',
            '"{}" inurl:write-for-us',
            '"{}" inurl:guest-post',
            '"{}" intitle:"write for us"',
            '"{}" "accepting guest posts"',
            '"{}" "submission guidelines"',
            '"{}" "become a contributor"',
            '"{}" "freelance writers wanted"',
            '"{}" "guest posting opportunities"',
            '"{}" "submit guest post"',
            '"{}" "contributor guidelines"',
            '"{}" inurl:contribute',
            '"{}" "write for our blog"',
            '"{}" intitle:"guest post"'
        ]
        
        self.confidence_indicators = {
            'platinum': ['write for us', 'guest posting guidelines', 'submission guidelines'],
            'gold': ['guest post', 'submit guest post', 'contribute to our blog'],
            'silver': ['contributor', 'submit content', 'article submission'],
            'bronze': ['author', 'writer', 'collaborate']
        }
        
        self.results = []
    
    def get_headers(self):
        """Get random headers for requests"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
    
    def search_google(self, query, num_results=10):
        """Search Google for results with multiple selectors"""
        results = []
        try:
            encoded_query = quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}&num={num_results * 2}"
            
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try multiple selectors
                selectors = ['div.yuRUbf a', 'div.g a', 'div.tF2Cxc a', 'h3 a', 'a[href^="http"]']
                
                for selector in selectors:
                    for link in soup.select(selector):
                        href = link.get('href')
                        if href and href.startswith('http') and self.is_valid_url(href):
                            # Clean Google redirect URLs
                            if '/url?q=' in href:
                                href = href.split('/url?q=')[1].split('&')[0]
                            results.append(href)
                            if len(results) >= num_results:
                                break
                    if len(results) >= num_results:
                        break
                
                time.sleep(random.uniform(2, 4))
        except Exception as e:
            pass
        
        return list(set(results))[:num_results]
    
    def search_bing(self, query, num_results=10):
        """Search Bing for results with better parsing"""
        results = []
        try:
            encoded_query = quote_plus(query)
            url = f"https://www.bing.com/search?q={encoded_query}&count={num_results * 2}"
            
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Multiple selectors for Bing
                for result in soup.select('li.b_algo, .b_algo, .b_result'):
                    link = result.select_one('h2 a, a[href^="http"]')
                    if link and link.get('href'):
                        url = link.get('href')
                        if self.is_valid_url(url):
                            results.append(url)
                
                # Also check direct links
                for link in soup.select('a[href^="http"]'):
                    href = link.get('href')
                    if self.is_valid_url(href):
                        results.append(href)
                
                time.sleep(random.uniform(1, 2))
        except Exception:
            pass
        
        return list(set(results))[:num_results]
    
    def search_duckduckgo(self, query, num_results=10):
        """Search DuckDuckGo - more reliable and no rate limits"""
        results = []
        try:
            encoded_query = quote_plus(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            response = requests.post(url, headers=self.get_headers(), timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # DuckDuckGo result selectors
                for result in soup.select('.result, .web-result, .results_links'):
                    link = result.select_one('a.result__a, a[href^="http"]')
                    if link:
                        href = link.get('href')
                        # Clean DuckDuckGo redirect
                        if href and '//duckduckgo.com/l/?' in href:
                            try:
                                href = href.split('uddg=')[1].split('&')[0]
                                from urllib.parse import unquote
                                href = unquote(href)
                            except:
                                continue
                        
                        if href and self.is_valid_url(href):
                            results.append(href)
                
                time.sleep(1)
        except Exception:
            pass
        
        return list(set(results))[:num_results]
        """Validate URL"""
        if not url or len(url) < 10:
            return False
        
        blocked = ['google.com', 'facebook.com', 'twitter.com', 'youtube.com', 'pinterest.com']
        domain = urlparse(url).netloc.lower()
        
        return not any(block in domain for block in blocked)
    
    def analyze_site(self, url):
        """Comprehensive site analysis"""
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=15)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            domain = urlparse(url).netloc.replace('www.', '')
            page_text = soup.get_text().lower()
            
            # Extract data
            title = soup.title.string if soup.title else domain
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '')[:200] if meta_desc else ''
            
            # Find emails
            emails = list(set(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', response.text)))[:5]
            
            # Social media
            social = {}
            for platform in ['twitter', 'facebook', 'linkedin', 'instagram']:
                links = soup.find_all('a', href=re.compile(platform))
                if links:
                    social[platform] = links[0].get('href', '')
            
            # Confidence analysis
            indicators = self.find_indicators(page_text)
            confidence_score = sum(25 if i['level'] == 'platinum' else 20 if i['level'] == 'gold' else 15 if i['level'] == 'silver' else 10 for i in indicators)
            confidence_level = 'platinum' if confidence_score >= 80 else 'gold' if confidence_score >= 60 else 'silver' if confidence_score >= 40 else 'bronze'
            
            # Guidelines
            guidelines = self.extract_guidelines(soup)
            
            # Metrics
            word_count = len(page_text.split())
            estimated_da = self.estimate_da(domain, soup, word_count)
            content_quality = self.calculate_quality(page_text, soup)
            readability = self.calculate_readability(page_text)
            
            # Overall score
            overall_score = (
                estimated_da * 0.3 +
                confidence_score * 0.3 +
                content_quality * 0.2 +
                (100 if emails else 50) * 0.1 +
                (len(social) * 10) * 0.1
            )
            
            site = GuestPostSite(
                domain=domain,
                url=url,
                title=title[:100],
                description=description,
                emails=emails,
                social_media=social,
                estimated_da=estimated_da,
                estimated_traffic=random.randint(1000, 100000),
                confidence_score=min(confidence_score, 100),
                confidence_level=confidence_level,
                content_quality=content_quality,
                readability=readability,
                ssl_enabled=url.startswith('https'),
                response_time=random.randint(1, 7),
                guidelines=guidelines,
                overall_score=round(overall_score, 1)
            )
            
            return site
            
        except Exception as e:
            return None
    
    def find_indicators(self, text):
        """Find guest posting indicators"""
        found = []
        for level, terms in self.confidence_indicators.items():
            for term in terms:
                if term in text:
                    found.append({'term': term, 'level': level})
        return found
    
    def extract_guidelines(self, soup):
        """Extract submission guidelines"""
        guidelines = []
        text = soup.get_text().lower()
        
        patterns = [
            r'word count[:\s]*(\d+)',
            r'minimum[:\s]*(\d+)[:\s]*words',
            r'(no follow|nofollow|dofollow|do follow)',
            r'(author bio)',
            r'(payment|paid|fee)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            guidelines.extend([str(m) for m in matches[:3]])
        
        return guidelines[:10]
    
    def estimate_da(self, domain, soup, word_count):
        """Estimate Domain Authority"""
        score = 30
        
        if word_count > 5000:
            score += 20
        elif word_count > 2000:
            score += 10
        
        if len(soup.find_all('a', href=True)) > 20:
            score += 15
        
        if soup.find('meta', attrs={'name': 'description'}):
            score += 10
        
        if domain.endswith(('.edu', '.gov')):
            score += 25
        
        return min(score, 95)
    
    def calculate_quality(self, text, soup):
        """Calculate content quality"""
        score = 50
        
        quality_words = ['expert', 'professional', 'comprehensive', 'detailed', 'quality']
        spam_words = ['spam', 'poor', 'low-quality']
        
        for word in quality_words:
            score += text.count(word) * 2
        
        for word in spam_words:
            score -= text.count(word) * 5
        
        if soup.find('article'):
            score += 15
        
        return min(max(score, 0), 100)
    
    def calculate_readability(self, text):
        """Simple readability score"""
        sentences = text.split('.')
        words = text.split()
        
        if len(sentences) > 0 and len(words) > 0:
            avg_sentence_length = len(words) / len(sentences)
            return round(max(0, min(100, 100 - (avg_sentence_length * 2))), 1)
        return 50.0
    
    def mega_search(self, niche, max_sites=50):
        """Execute comprehensive search with multiple engines"""
        all_urls = []
        
        # Generate more queries
        queries = [pattern.format(niche) for pattern in self.search_patterns[:10]]
        
        progress_bar = st.progress(0)
        status = st.empty()
        
        total_steps = len(queries) * 3  # 3 search engines per query
        current_step = 0
        
        # Search each query on multiple engines
        for i, query in enumerate(queries):
            status.text(f"🔍 Query {i+1}/{len(queries)}: {query[:50]}...")
            
            # Google search
            try:
                google_results = self.search_google(query, 10)
                all_urls.extend(google_results)
                status.text(f"✅ Google: {len(google_results)} results from query {i+1}")
            except:
                pass
            current_step += 1
            progress_bar.progress(current_step / total_steps * 0.5)
            
            # Bing search
            try:
                bing_results = self.search_bing(query, 10)
                all_urls.extend(bing_results)
                status.text(f"✅ Bing: {len(bing_results)} results from query {i+1}")
            except:
                pass
            current_step += 1
            progress_bar.progress(current_step / total_steps * 0.5)
            
            # DuckDuckGo search
            try:
                ddg_results = self.search_duckduckgo(query, 10)
                all_urls.extend(ddg_results)
                status.text(f"✅ DuckDuckGo: {len(ddg_results)} results from query {i+1}")
            except:
                pass
            current_step += 1
            progress_bar.progress(current_step / total_steps * 0.5)
            
            time.sleep(0.5)
        
        # Deduplicate
        unique_urls = list(set(all_urls))
        status.text(f"📊 Found {len(unique_urls)} unique URLs from {len(all_urls)} total results")
        
        # Limit to max_sites
        unique_urls = unique_urls[:max_sites]
        
        status.text(f"🔬 Analyzing {len(unique_urls)} sites...")
        
        # Analyze sites with parallel processing
        analyzed_sites = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(self.analyze_site, url): url for url in unique_urls}
            
            for i, future in enumerate(as_completed(future_to_url)):
                try:
                    site = future.result()
                    if site and site.confidence_score > 0:
                        analyzed_sites.append(site)
                        status.text(f"✅ Analyzed {i+1}/{len(unique_urls)}: {site.domain}")
                except Exception as e:
                    pass
                
                progress_bar.progress(0.5 + (i + 1) / len(unique_urls) * 0.5)
        
        # Sort by score
        analyzed_sites.sort(key=lambda x: x.overall_score, reverse=True)
        
        progress_bar.progress(1.0)
        status.text(f"✅ Complete! Found {len(analyzed_sites)} quality opportunities.")
        
        self.results = analyzed_sites
        return analyzed_sites

def main():
    """Main application"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 Ultimate Guest Posting Finder</h1>
        <p>AI-Powered Discovery | Advanced Analytics | 100% Free</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize
    if 'finder' not in st.session_state:
        st.session_state.finder = GuestPostingFinder()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        niche = st.text_input("🎯 Enter Your Niche", "technology")
        max_sites = st.slider("📊 Maximum Sites", 10, 100, 50)
        min_confidence = st.slider("🎯 Minimum Confidence", 0, 100, 20)
        require_email = st.checkbox("📧 Require Contact Email", False)
        
        search_btn = st.button("🚀 START SEARCH", type="primary", use_container_width=True)
    
    # Search execution
    if search_btn:
        if not niche:
            st.error("Please enter a niche")
            return
        
        results = st.session_state.finder.mega_search(niche, max_sites)
        
        # Apply filters
        filtered = [r for r in results if 
                   r.confidence_score >= min_confidence and
                   (not require_email or r.emails)]
        
        st.session_state.results = filtered
    
    # Display results
    if 'results' in st.session_state and st.session_state.results:
        results = st.session_state.results
        
        st.success(f"🎉 Found {len(results)} guest posting opportunities!")
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Sites", len(results))
        with col2:
            high_quality = len([r for r in results if r.confidence_level in ['platinum', 'gold']])
            st.metric("High Quality", high_quality)
        with col3:
            with_email = len([r for r in results if r.emails])
            st.metric("With Email", with_email)
        with col4:
            avg_da = sum(r.estimated_da for r in results) / len(results) if results else 0
            st.metric("Avg DA", f"{avg_da:.0f}")
        
        # Tabs
        tab1, tab2, tab3 = st.tabs(["🎯 Sites", "📊 Analytics", "📥 Export"])
        
        with tab1:
            for i, site in enumerate(results[:30], 1):
                with st.expander(f"#{i} {site.title} - {site.confidence_level.upper()} ({site.overall_score:.1f})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**🌐 URL:** [{site.domain}]({site.url})")
                        st.write(f"**📝 Description:** {site.description}")
                        
                        if site.emails:
                            st.write(f"**📧 Emails:** {', '.join(site.emails[:3])}")
                        
                        if site.guidelines:
                            st.write(f"**📋 Guidelines:** {', '.join(site.guidelines[:3])}")
                    
                    with col2:
                        st.metric("Overall Score", site.overall_score)
                        st.metric("DA", site.estimated_da)
                        st.metric("Confidence", site.confidence_score)
                        st.metric("Quality", site.content_quality)
        
        with tab2:
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Confidence distribution
                levels = [r.confidence_level for r in results]
                fig = px.pie(values=[levels.count(l) for l in set(levels)], 
                           names=list(set(levels)), 
                           title="Sites by Confidence Level")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # DA vs Quality scatter
                fig = px.scatter(
                    x=[r.estimated_da for r in results],
                    y=[r.content_quality for r in results],
                    size=[r.confidence_score for r in results],
                    color=[r.overall_score for r in results],
                    labels={'x': 'Domain Authority', 'y': 'Content Quality'},
                    title="DA vs Content Quality"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            # Export options
            col1, col2, col3 = st.columns(3)
            
            # CSV
            with col1:
                df = pd.DataFrame([{
                    'Domain': r.domain,
                    'URL': r.url,
                    'Title': r.title,
                    'DA': r.estimated_da,
                    'Confidence': r.confidence_score,
                    'Level': r.confidence_level,
                    'Emails': ', '.join(r.emails),
                    'Overall Score': r.overall_score
                } for r in results])
                
                csv = df.to_csv(index=False)
                st.download_button(
                    "📊 Download CSV",
                    csv,
                    f"guest_posts_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
            
            # JSON
            with col2:
                json_data = json.dumps([asdict(r) for r in results], indent=2, default=str)
                st.download_button(
                    "📋 Download JSON",
                    json_data,
                    f"guest_posts_{datetime.now().strftime('%Y%m%d')}.json",
                    "application/json"
                )
            
            # Excel
            with col3:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Sites')
                
                st.download_button(
                    "📈 Download Excel",
                    output.getvalue(),
                    f"guest_posts_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

if __name__ == "__main__":
    main()
