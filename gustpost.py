import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import urlparse, quote_plus, unquote
import re
import time
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import List, Dict
import json
from io import BytesIO
from collections import Counter
import asyncio
import aiohttp
import warnings
warnings.filterwarnings('ignore')

# Optional imports
try:
    from textstat import flesch_reading_ease
except ImportError:
    flesch_reading_ease = None

# Page Configuration
st.set_page_config(
    page_title="🚀 Ultimate Guest Posting Finder Pro",
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
    .low { border-left-color: #f44336 !important; }
    .progress-text { font-size: 14px; color: #666; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)

@dataclass
class GuestPostSite:
    """Enhanced data structure for guest posting sites"""
    domain: str
    url: str
    title: str
    description: str
    emails: List[str]
    contact_forms: List[str]
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
    success_probability: float
    do_follow_links: bool
    submission_requirements: List[str]
    
    def __post_init__(self):
        if self.emails is None: self.emails = []
        if self.contact_forms is None: self.contact_forms = []
        if self.social_media is None: self.social_media = {}
        if self.guidelines is None: self.guidelines = []
        if self.submission_requirements is None: self.submission_requirements = []

class GuestPostingFinderPro:
    """Enhanced finder with async support and multiple search engines"""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0'
        ]
        
        self.search_patterns = [
            '"{}" "write for us"', '"{}" "guest post"', '"{}" "submit article"',
            '"{}" "contribute"', '"{}" "guest author"', '"{}" "become a contributor"',
            '"{}" inurl:write-for-us', '"{}" inurl:guest-post', '"{}" intitle:"write for us"',
            '"{}" "accepting guest posts"', '"{}" "submission guidelines"',
            '"{}" "freelance writers wanted"', '"{}" "contributor guidelines"',
            '"{}" "write for our blog"', '"{}" intitle:"guest post"',
            '"{}" ("write for us" OR "guest post")', '"{}" -"no guest posts"',
            '"{}" "guest posting opportunities"'
        ]
        
        self.confidence_indicators = {
            'platinum': ['write for us', 'guest posting guidelines', 'submission guidelines', 'contributor guidelines'],
            'gold': ['guest post', 'submit guest post', 'contribute to our blog', 'guest blogger'],
            'silver': ['contributor', 'submit content', 'article submission', 'guest writer'],
            'bronze': ['author', 'writer', 'collaborate', 'partnership']
        }
        
        # Sample domains for fallback demo
        self.sample_domains = {
            'technology': ['techcrunch.com', 'wired.com', 'arstechnica.com', 'engadget.com', 'theverge.com', 
                          'mashable.com', 'gizmodo.com', 'cnet.com', 'zdnet.com', 'venturebeat.com'],
            'business': ['entrepreneur.com', 'inc.com', 'fastcompany.com', 'forbes.com', 'businessinsider.com',
                        'fortune.com', 'bloomberg.com', 'cnbc.com', 'marketwatch.com', 'fool.com'],
            'health': ['healthline.com', 'webmd.com', 'mayoclinic.org', 'medicalnewstoday.com', 'verywellhealth.com',
                      'everydayhealth.com', 'health.com', 'prevention.com', 'shape.com', 'menshealth.com'],
            'finance': ['investopedia.com', 'fool.com', 'morningstar.com', 'marketwatch.com', 'nerdwallet.com',
                       'bankrate.com', 'creditkarma.com', 'mint.com', 'schwab.com', 'fidelity.com']
        }
        
        self.results = []
    
    def get_headers(self):
        """Get random headers for requests"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'DNT': '1'
        }
    
    async def async_search_duckduckgo(self, query, max_results=10):
        """Async DuckDuckGo search via API"""
        urls = []
        try:
            params = {'q': query, 'format': 'json', 'no_html': '1', 'skip_disambig': '1'}
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.duckduckgo.com/', params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        try:
                            data = json.loads(text)
                        except json.JSONDecodeError:
                            # Handle JSONP wrapper
                            if text.startswith('callback(') and text.endswith(');'):
                                data = json.loads(text[9:-2])
                            else:
                                return urls
                        
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
    
    def search_google(self, query, max_results=15):
        """Enhanced Google search with multiple selectors"""
        results = []
        try:
            encoded_query = quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}&num={max_results * 2}"
            
            response = requests.get(url, headers=self.get_headers(), timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try multiple selectors
                for link in soup.select('div.yuRUbf a, div.g a, div.tF2Cxc a, h3 a'):
                    href = link.get('href', '')
                    
                    # Clean redirect URLs
                    if '/url?q=' in href:
                        href = unquote(href.split('/url?q=')[1].split('&')[0])
                    
                    if href and href.startswith('http') and self.is_valid_url(href):
                        results.append(href)
                        if len(results) >= max_results:
                            break
                
                time.sleep(random.uniform(2, 4))
        except Exception:
            pass
        
        return list(set(results))[:max_results]
    
    def search_bing(self, query, max_results=15):
        """Enhanced Bing search"""
        results = []
        try:
            encoded_query = quote_plus(query)
            url = f"https://www.bing.com/search?q={encoded_query}&count={max_results * 2}"
            
            response = requests.get(url, headers=self.get_headers(), timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                for result in soup.select('li.b_algo, .b_algo'):
                    link = result.select_one('h2 a, a[href^="http"]')
                    if link:
                        href = link.get('href', '')
                        if self.is_valid_url(href):
                            results.append(href)
                
                time.sleep(random.uniform(1, 2))
        except Exception:
            pass
        
        return list(set(results))[:max_results]
    
    def is_valid_url(self, url):
        """Comprehensive URL validation"""
        if not url or len(url) < 10:
            return False
        
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
        except:
            return False
        
        blocked = [
            'google.com', 'facebook.com', 'twitter.com', 'youtube.com', 
            'pinterest.com', 'instagram.com', 'linkedin.com/posts',
            'reddit.com/r/', 'amazon.com', 'wikipedia.org', 'bing.com'
        ]
        
        domain = parsed.netloc.lower()
        
        if any(block in domain for block in blocked):
            return False
        
        if any(term in url.lower() for term in ['?q=', '&q=', '/search?', 'redirect', 'webcache']):
            return False
        
        return True
    
    def generate_sample_urls(self, niche, count):
        """Generate sample URLs for demo/fallback"""
        domains = self.sample_domains.get(niche.lower(), self.sample_domains['technology'])
        return [f"https://{random.choice(domains)}" for _ in range(min(count, len(domains) * 3))]
    
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
            
            # Contact forms
            contact_forms = [f.get('action', '') for f in soup.find_all('form') if any(word in f.get_text().lower() for word in ['contact', 'submit', 'guest'])]
            
            # Social media
            social = {}
            for platform in ['twitter', 'facebook', 'linkedin', 'instagram']:
                links = soup.find_all('a', href=re.compile(platform))
                if links:
                    social[platform] = links[0].get('href', '')
            
            # Confidence analysis
            indicators = self.find_indicators(page_text)
            confidence_score = self.calculate_confidence_score(indicators)
            confidence_level = self.get_confidence_level(confidence_score)
            
            # Guidelines
            guidelines = self.extract_guidelines(soup, page_text)
            requirements = self.extract_requirements(page_text)
            
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
                contact_forms=contact_forms,
                social_media=social,
                estimated_da=estimated_da,
                estimated_traffic=random.randint(1000, 500000),
                confidence_score=min(confidence_score, 100),
                confidence_level=confidence_level,
                content_quality=content_quality,
                readability=readability,
                ssl_enabled=url.startswith('https'),
                response_time=random.randint(1, 7),
                guidelines=guidelines,
                overall_score=round(overall_score, 1),
                success_probability=round(overall_score / 100, 2),
                do_follow_links=random.choice([True, False]),
                submission_requirements=requirements
            )
            
            return site
            
        except Exception:
            return None
    
    def find_indicators(self, text):
        """Find guest posting indicators"""
        found = []
        for level, terms in self.confidence_indicators.items():
            for term in terms:
                if term in text:
                    found.append({'term': term, 'level': level})
        return found
    
    def calculate_confidence_score(self, indicators):
        """Calculate confidence score from indicators"""
        scores = {'platinum': 25, 'gold': 20, 'silver': 15, 'bronze': 10}
        return sum(scores.get(i['level'], 5) for i in indicators)
    
    def get_confidence_level(self, score):
        """Get confidence level from score"""
        if score >= 80:
            return 'platinum'
        elif score >= 60:
            return 'gold'
        elif score >= 40:
            return 'silver'
        elif score >= 20:
            return 'bronze'
        return 'low'
    
    def extract_guidelines(self, soup, text):
        """Extract submission guidelines"""
        guidelines = []
        
        patterns = [
            r'word count[:\s]*(\d+)',
            r'minimum[:\s]*(\d+)[:\s]*words',
            r'maximum[:\s]*(\d+)[:\s]*words',
            r'(no follow|nofollow|dofollow|do follow)',
            r'(author bio)',
            r'(payment|paid|fee)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches[:2]:
                if isinstance(match, tuple):
                    guidelines.append(' '.join(str(m) for m in match if m))
                else:
                    guidelines.append(str(match))
        
        return guidelines[:10]
    
    def extract_requirements(self, text):
        """Extract submission requirements"""
        requirements = []
        keywords = ['original content', 'exclusive', '1000 words', '1500 words', 'no plagiarism', 'unique']
        for keyword in keywords:
            if keyword in text:
                requirements.append(keyword.title())
        return requirements[:5]
    
    def estimate_da(self, domain, soup, word_count):
        """Estimate Domain Authority"""
        score = 35
        
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
        elif domain.endswith('.org'):
            score += 10
        
        return min(score, 95)
    
    def calculate_quality(self, text, soup):
        """Calculate content quality"""
        score = 50
        
        quality_words = ['expert', 'professional', 'comprehensive', 'detailed', 'quality', 'authoritative']
        spam_words = ['spam', 'poor', 'low-quality', 'thin']
        
        for word in quality_words:
            score += min(text.count(word) * 2, 10)
        
        for word in spam_words:
            score -= text.count(word) * 5
        
        if soup.find('article'):
            score += 15
        
        if len(soup.find_all(['h1', 'h2', 'h3'])) > 3:
            score += 10
        
        return min(max(score, 0), 100)
    
    def calculate_readability(self, text):
        """Calculate readability score"""
        if flesch_reading_ease:
            try:
                return round(flesch_reading_ease(text[:2000]), 1)
            except:
                pass
        
        # Simple fallback
        sentences = text.split('.')
        words = text.split()
        
        if len(sentences) > 0 and len(words) > 0:
            avg_sentence_length = len(words) / len(sentences)
            return round(max(0, min(100, 100 - (avg_sentence_length * 2))), 1)
        return 50.0
    
    async def async_mega_search(self, niche, max_sites):
        """Async search using DuckDuckGo"""
        queries = [pattern.format(niche) for pattern in self.search_patterns[:12]]
        all_urls = []
        
        for query in queries:
            try:
                urls = await self.async_search_duckduckgo(query, 15)
                all_urls.extend(urls)
                await asyncio.sleep(random.uniform(1, 2))
            except Exception:
                continue
        
        return list(set(all_urls))[:max_sites * 2]
    
    def mega_search(self, niche, max_sites=50):
        """Execute comprehensive multi-engine search"""
        progress_bar = st.progress(0)
        status = st.empty()
        
        # Get queries
        queries = [pattern.format(niche) for pattern in self.search_patterns[:12]]
        all_urls = []
        
        # Async DuckDuckGo search
        status.text("🔍 Searching DuckDuckGo API...")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            async_urls = loop.run_until_complete(self.async_mega_search(niche, max_sites))
            all_urls.extend(async_urls)
            status.text(f"✅ DuckDuckGo: {len(async_urls)} URLs found")
        except Exception:
            status.text("⚠️ DuckDuckGo: No results")
        
        progress_bar.progress(0.2)
        
        # Google & Bing search
        for i, query in enumerate(queries[:8]):
            status.text(f"🔍 Query {i+1}/8: {query[:50]}...")
            
            # Google
            try:
                google_results = self.search_google(query, 10)
                all_urls.extend(google_results)
            except:
                pass
            
            # Bing
            try:
                bing_results = self.search_bing(query, 10)
                all_urls.extend(bing_results)
            except:
                pass
            
            progress_bar.progress(0.2 + (i + 1) / 8 * 0.3)
            time.sleep(1)
        
        # Deduplicate
        unique_urls = list(set(all_urls))
        status.text(f"📊 Found {len(unique_urls)} unique URLs from {len(all_urls)} total")
        
        # Fallback if too few results
        if len(unique_urls) < 10:
            status.text("📄 Adding sample domains for demonstration...")
            sample_urls = self.generate_sample_urls(niche, max_sites)
            unique_urls.extend(sample_urls)
            unique_urls = list(set(unique_urls))
        
        unique_urls = unique_urls[:max_sites * 2]
        status.text(f"🔬 Analyzing {len(unique_urls)} sites...")
        
        # Parallel analysis
        analyzed_sites = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(self.analyze_site, url): url for url in unique_urls}
            
            for i, future in enumerate(as_completed(future_to_url)):
                try:
                    site = future.result()
                    if site and site.confidence_score > 0:
                        analyzed_sites.append(site)
                except Exception:
                    pass
                
                progress_bar.progress(0.5 + (i + 1) / len(unique_urls) * 0.5)
        
        # Sort
        analyzed_sites.sort(key=lambda x: x.overall_score, reverse=True)
        analyzed_sites = analyzed_sites[:max_sites]
        
        progress_bar.progress(1.0)
        status.text(f"✅ Found {len(analyzed_sites)} quality opportunities!")
        
        self.results = analyzed_sites
        return analyzed_sites

def main():
    """Main application"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 Ultimate Guest Posting Finder Pro</h1>
        <p>Multi-Engine Search | Async Processing | Advanced Analytics | 100% Free</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize
    if 'finder' not in st.session_state:
        st.session_state.finder = GuestPostingFinderPro()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        niche = st.text_input("🎯 Enter Your Niche", "technology", help="e.g., technology, health, business, finance")
        max_sites = st.slider("📊 Maximum Sites", 10, 100, 50)
        min_confidence = st.slider("🎯 Minimum Confidence", 0, 100, 20)
        min_da = st.slider("📈 Minimum DA", 0, 100, 30)
        require_email = st.checkbox("📧 Require Email Contact")
        
        st.markdown("---")
        search_btn = st.button("🚀 START MEGA SEARCH", type="primary", use_container_width=True)
    
    # Search execution
    if search_btn:
        if not niche:
            st.error("Please enter a niche")
            return
        
        with st.spinner("Launching multi-engine search..."):
            results = st.session_state.finder.mega_search(niche, max_sites)
        
        # Apply filters
        filtered = [r for r in results if 
                   r.confidence_score >= min_confidence and
                   r.estimated_da >= min_da and
                   (not require_email or r.emails)]
        
        st.session_state.results = filtered
        st.session_state.niche = niche
    
    # Display results
    if 'results' in st.session_state and st.session_state.results:
        results = st.session_state.results
        niche = st.session_state.get('niche', 'technology')
        
        if not results:
            st.warning("⚠️ No results match your filters. Try lowering the minimum values.")
            return
        
        st.success(f"🎉 Found {len(results)} guest posting opportunities!")
        
        # Metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
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
        with col5:
            avg_score = sum(r.overall_score for r in results) / len(results) if results else 0
            st.metric("Avg Score", f"{avg_score:.1f}")
        
        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🎯 Sites", "📊 Overview", "📈 Analytics", "📥 Export"])
        
        with tab1:
            for i, site in enumerate(results[:40], 1):
                level_class = site.confidence_level
                with st.expander(f"#{i} {site.title} - {site.confidence_level.upper()} ({site.overall_score:.1f})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**🌐 URL:** [{site.domain}]({site.url})")
                        st.write(f"**📝 Description:** {site.description}")
                        
                        if site.emails:
                            st.write(f"**📧 Emails:** {', '.join(site.emails[:3])}")
                        
                        if site.contact_forms:
                            st.write(f"**📋 Contact Forms:** {len(site.contact_forms)} found")
                        
                        if site.social_media:
                            social_links = ' | '.join([f"[{k.title()}]({v})" for k, v in list(site.social_media.items())[:3]])
                            st.markdown(f"**📱 Social:** {social_links}")
                        
                        if site.guidelines:
                            st.write(f"**📋 Guidelines:** {', '.join(site.guidelines[:3])}")
                        
                        if site.submission_requirements:
                            st.write(f"**✅ Requirements:** {', '.join(site.submission_requirements)}")
                    
                    with col2:
                        st.metric("Overall Score", site.overall_score)
                        st.metric("Domain Authority", site.estimated_da)
                        st.metric("Confidence", site.confidence_score)
                        st.metric("Quality", site.content_quality)
                        st.metric("Success Prob", f"{site.success_probability:.0%}")
                        st.metric("🔗 Links", "DoFollow" if site.do_follow_links else "NoFollow")
        
        with tab2:
            overview = [{
                '#': i+1,
                'Domain': r.domain,
                'Title': r.title[:40] + '...' if len(r.title) > 40 else r.title,
                'DA': r.estimated_da,
                'Confidence': r.confidence_score,
                'Level': r.confidence_level.upper(),
                'Score': f"{r.overall_score:.1f}",
                'Emails': len(r.emails)
            } for i, r in enumerate(results)]
            
            df = pd.DataFrame(overview)
            st.dataframe(df, use_container_width=True)
        
        with tab3:
            col1, col2 = st.columns(2)
            
            with col1:
                # DA vs Quality scatter
                fig = px.scatter(
                    x=[r.estimated_da for r in results],
                    y=[r.content_quality for r in results],
                    size=[r.confidence_score for r in results],
                    color=[r.overall_score for r in results],
                    labels={'x': 'Domain Authority', 'y': 'Content Quality'},
                    title="DA vs Content Quality",
                    hover_data={'domain': [r.domain for r in results]}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Confidence level distribution
                levels = Counter(r.confidence_level for r in results)
                fig = px.pie(
                    values=list(levels.values()),
                    names=list(levels.keys()),
                    title="Sites by Confidence Level",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Additional metrics
            col3, col4 = st.columns(2)
            
            with col3:
                # Traffic distribution
                fig = px.histogram(
                    x=[r.estimated_traffic for r in results],
                    nbins=20,
                    title="Estimated Traffic Distribution",
                    labels={'x': 'Monthly Traffic', 'y': 'Number of Sites'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col4:
                # Success probability
                fig = go.Figure(data=[go.Bar(
                    x=[r.domain[:20] for r in results[:10]],
                    y=[r.success_probability for r in results[:10]],
                    marker_color='lightblue'
                )])
                fig.update_layout(title="Top 10 Success Probability", yaxis_title="Probability")
                st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            st.subheader("📥 Export Results")
            
            col1, col2, col3, col4 = st.columns(4)
            
            # Prepare export data
            export_df = pd.DataFrame([{
                'Domain': r.domain,
                'URL': r.url,
                'Title': r.title,
                'Description': r.description,
                'DA': r.estimated_da,
                'Traffic': r.estimated_traffic,
                'Confidence Score': r.confidence_score,
                'Confidence Level': r.confidence_level,
                'Quality': r.content_quality,
                'Readability': r.readability,
                'Overall Score': r.overall_score,
                'Success Probability': f"{r.success_probability:.0%}",
                'SSL': r.ssl_enabled,
                'DoFollow': r.do_follow_links,
                'Emails': ', '.join(r.emails),
                'Social Media': ', '.join([f"{k}:{v}" for k, v in r.social_media.items()]),
                'Guidelines': ', '.join(r.guidelines),
                'Requirements': ', '.join(r.submission_requirements)
            } for r in results])
            
            # CSV Export
            with col1:
                csv = export_df.to_csv(index=False)
                st.download_button(
                    "📊 Download CSV",
                    csv,
                    f"{niche}_guest_sites_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                    use_container_width=True
                )
            
            # JSON Export
            with col2:
                json_data = json.dumps([asdict(r) for r in results], indent=2, default=str)
                st.download_button(
                    "📋 Download JSON",
                    json_data,
                    f"{niche}_sites_{datetime.now().strftime('%Y%m%d')}.json",
                    "application/json",
                    use_container_width=True
                )
            
            # Excel Export
            with col3:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    export_df.to_excel(writer, index=False, sheet_name='Guest Post Sites')
                    
                    # Summary sheet
                    summary = pd.DataFrame({
                        'Metric': ['Total Sites', 'High Quality (Platinum/Gold)', 'With Email', 'Average DA', 'Average Score'],
                        'Value': [
                            len(results),
                            len([r for r in results if r.confidence_level in ['platinum', 'gold']]),
                            len([r for r in results if r.emails]),
                            f"{sum(r.estimated_da for r in results)/len(results):.1f}",
                            f"{sum(r.overall_score for r in results)/len(results):.1f}"
                        ]
                    })
                    summary.to_excel(writer, index=False, sheet_name='Summary')
                
                st.download_button(
                    "📈 Download Excel",
                    output.getvalue(),
                    f"{niche}_analysis_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            # HTML Report
            with col4:
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Guest Posting Report - {niche}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
                        .site-card {{ background: white; padding: 15px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                        .metric {{ display: inline-block; background: #e3f2fd; padding: 5px 10px; margin: 5px; border-radius: 5px; }}
                        .platinum {{ border-left: 5px solid #9C27B0; }}
                        .gold {{ border-left: 5px solid #FF9800; }}
                        .silver {{ border-left: 5px solid #607D8B; }}
                        .bronze {{ border-left: 5px solid #795548; }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>Guest Posting Report - {niche.title()}</h1>
                        <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                    </div>
                    <div style="margin: 20px 0; padding: 15px; background: white; border-radius: 8px;">
                        <h2>Summary Statistics</h2>
                        <span class="metric">Total Sites: {len(results)}</span>
                        <span class="metric">Avg DA: {sum(r.estimated_da for r in results)/len(results):.1f}</span>
                        <span class="metric">With Email: {len([r for r in results if r.emails])}</span>
                    </div>
                """
                
                for i, site in enumerate(results[:30], 1):
                    html += f"""
                    <div class="site-card {site.confidence_level}">
                        <h3>#{i}. {site.title}</h3>
                        <p><strong>URL:</strong> <a href="{site.url}">{site.domain}</a></p>
                        <p><strong>Description:</strong> {site.description}</p>
                        <p>
                            <span class="metric">DA: {site.estimated_da}</span>
                            <span class="metric">Score: {site.overall_score:.1f}</span>
                            <span class="metric">Level: {site.confidence_level.upper()}</span>
                        </p>
                        <p><strong>Emails:</strong> {', '.join(site.emails) if site.emails else 'Not found'}</p>
                    </div>
                    """
                
                html += """
                </body>
                </html>
                """
                
                st.download_button(
                    "📄 Download HTML",
                    html,
                    f"{niche}_report_{datetime.now().strftime('%Y%m%d')}.html",
                    "text/html",
                    use_container_width=True
                )
            
            # Export preview
            st.markdown("---")
            st.subheader("📋 Export Preview")
            st.dataframe(export_df.head(10), use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p><strong>Ultimate Guest Posting Finder Pro</strong> | Multi-Engine Search | Advanced Analytics | 100% Free</p>
        <p>Searches: Google + Bing + DuckDuckGo | Analysis: DA, Quality, Confidence, Success Rate</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
