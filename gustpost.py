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
from collections import Counter, defaultdict
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
.main-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; color: white; text-align: center; margin-bottom: 2rem; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
.metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 12px; color: white; text-align: center; margin: 0.5rem 0; box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
.site-card { background: white; padding: 1.5rem; border-radius: 12px; margin: 1rem 0; box-shadow: 0 5px 20px rgba(0,0,0,0.1); border-left: 5px solid #4CAF50; }
.platinum-site { border-left-color: #9C27B0 !important; }
.gold-site { border-left-color: #FF9800 !important; }
.silver-site { border-left-color: #607D8B !important; }
.bronze-site { border-left-color: #795548 !important; }
</style>
""", unsafe_allow_html=True)

@dataclass
class GuestPostSite:
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
    cms_platform: str = "Unknown"
    
    def __post_init__(self):
        if self.emails is None: self.emails = []
        if self.contact_forms is None: self.contact_forms = []
        if self.phone_numbers is None: self.phone_numbers = []
        if self.social_media is None: self.social_media = {}
        if self.submission_requirements is None: self.submission_requirements = []
        if self.preferred_topics is None: self.preferred_topics = []

class GuestPostingFinder:
    SEARCH_PATTERNS = [
        # === VERY LOW LEVEL (Basic Footprints) ===
        '"{}" "write for us"',
        '"{}" "guest post"',
        '"{}" "contribute"',
        '"{}" "submit article"',
        '"{}" "guest author"',
        '"{}" write for us',
        '"{}" guest post',
        '"{}" contribute article',
        '"{}" submit post',
        
        # === LOW LEVEL (Common Variations) ===
        '"{}" "become a contributor"',
        '"{}" "guest blogger"',
        '"{}" "freelance writer"',
        '"{}" "submit content"',
        '"{}" "write for our blog"',
        '"{}" "accepting guest posts"',
        '"{}" "guest posting guidelines"',
        '"{}" "submission guidelines"',
        '"{}" "contributor guidelines"',
        '"{}" "writers wanted"',
        '"{}" "looking for contributors"',
        '"{}" "guest column"',
        '"{}" "guest article"',
        '"{}" "submit guest post"',
        '"{}" "contribute to our blog"',
        
        # === MID LEVEL (URL & Title Operators) ===
        '"{}" inurl:write-for-us',
        '"{}" inurl:guest-post',
        '"{}" inurl:guest-author',
        '"{}" inurl:contribute',
        '"{}" inurl:submit-post',
        '"{}" inurl:submission-guidelines',
        '"{}" inurl:contributor-guidelines',
        '"{}" inurl:write-guest-post',
        'intitle:"{}" "write for us"',
        'intitle:"write for us" "{}"',
        'intitle:"{}" "guest post"',
        'intitle:"guest post" "{}"',
        'intitle:"{}" "contribute"',
        'intitle:"contribute" "{}"',
        'intitle:"{}" "submit article"',
        'intitle:"submission guidelines" "{}"',
        
        # === HIGH LEVEL (Advanced Operators) ===
        '"{}" ("write for us" OR "guest post" OR "contribute")',
        '"{}" ("contributor" OR "guest author" OR "freelance writer")',
        '"{}" (inurl:write-for-us OR inurl:guest-post)',
        '"{}" (intitle:"write for us" OR intitle:"guest post")',
        '"{}" "write for us" -"not accepting"',
        '"{}" "guest post" -"closed"',
        '"{}" "contribute" -"suspended"',
        '"write for us" "{}" -"no longer"',
        '"guest post" "{}" -"not currently"',
        
        # === PEAK LEVEL (CMS & Platform Specific) ===
        '"{}" "powered by wordpress" "write for us"',
        '"{}" "powered by wordpress" "guest post"',
        '"{}" "powered by drupal" "contribute"',
        '"{}" "powered by ghost" "guest author"',
        '"{}" "powered by jekyll" "submit"',
        '"{}" "built with hugo" "write for us"',
        '"{}" site:medium.com "write"',
        '"{}" site:medium.com "contribute"',
        '"{}" site:linkedin.com "guest post"',
        '"{}" site:linkedin.com/pulse "write"',
        '"{}" site:dev.to "guest post"',
        '"{}" site:hashnode.com "write for us"',
        '"{}" site:substack.com "guest author"',
        '"{}" site:hackernoon.com "contribute"',
        '"{}" site:towards.dev "write for us"',
        '"{}" site:reddit.com "guest posting"',
        
        # === SECRETS & HIDDEN (Reverse Engineering) ===
        '"{}" "this is a guest post"',
        '"{}" "this guest post"',
        '"{}" "today\'s guest author"',
        '"{}" "guest post by"',
        '"{}" "written by guest"',
        '"{}" "contributed by"',
        '"{}" "post submitted by"',
        '"{}" "article by guest"',
        '"{}" intext:"guest post by"',
        '"{}" intext:"contributed by"',
        '"{}" "we welcome guest posts"',
        '"{}" "we accept guest posts"',
        '"{}" "guest posts accepted"',
        '"{}" "accepting contributions"',
        '"{}" "open to guest posts"',
        
        # === HIDDEN (Contact & Submission Discovery) ===
        '"{}" "submit your article"',
        '"{}" "pitch your idea"',
        '"{}" "pitch us"',
        '"{}" "want to write for"',
        '"{}" "interested in contributing"',
        '"{}" "editorial calendar"',
        '"{}" "content submission"',
        '"{}" "article submission"',
        '"{}" "blog submission"',
        '"{}" "guest post opportunity"',
        '"{}" "blogging opportunity"',
        '"{}" "writing opportunity"',
        
        # === SECRETS (Email & Contact Patterns) ===
        '"{}" "email" "guest post"',
        '"{}" "contact" "contribute"',
        '"{}" "editor" "submit"',
        '"{}" "pitch" "article"',
        '"{}" intext:"email us" "guest post"',
        '"{}" intext:"contact us" "contribute"',
        
        # === HIDDEN (File Type Searches) ===
        '"{}" filetype:pdf "submission guidelines"',
        '"{}" filetype:pdf "writer guidelines"',
        '"{}" filetype:pdf "contributor guidelines"',
        '"{}" filetype:doc "guest post guidelines"',
        '"{}" filetype:docx "write for us"',
        
        # === SECRETS (Social Proof & Backdoors) ===
        '"{}" "guest post disclaimer"',
        '"{}" "sponsored post"',
        '"{}" "partner content"',
        '"{}" "external contributor"',
        '"{}" "community contributor"',
        '"{}" "featured contributor"',
        '"{}" "expert contributor"',
        '"{}" "industry expert" "write for us"',
        '"{}" "thought leader" "contribute"',
        
        # === PEAK SECRETS (Domain Extensions) ===
        '"{}" site:.edu "write for us"',
        '"{}" site:.edu "guest post"',
        '"{}" site:.org "contribute"',
        '"{}" site:.gov "submit article"',
        '"{}" site:.io "write for us"',
        '"{}" site:.co "guest post"',
        
        # === HIDDEN (Niche Blog Networks) ===
        '"{}" "blog network" "write for us"',
        '"{}" "contributor network"',
        '"{}" "writers network"',
        '"{}" "blogging community" "contribute"',
        
        # === SECRETS (Time-Based Discovery) ===
        '"{}" "write for us" after:2023',
        '"{}" "guest post" after:2023',
        '"{}" "now accepting" "guest posts"',
        '"{}" "currently accepting" "submissions"',
        '"{}" "open for submissions"',
        
        # === PEAK HIDDEN (Competitor Analysis) ===
        '"{}" "featured on"',
        '"{}" "as seen on"',
        '"{}" "published on"',
        '"{}" "mentioned in"',
        '"{}" "press coverage"',
        
        # === ULTIMATE SECRETS (Unconventional Patterns) ===
        '"{}" "guest contributor wanted"',
        '"{}" "seeking guest writers"',
        '"{}" "call for submissions"',
        '"{}" "call for contributors"',
        '"{}" "submit your story"',
        '"{}" "share your expertise"',
        '"{}" "share your knowledge"',
        '"{}" "industry insights wanted"',
        '"{}" "expert roundup" "contribute"',
        '"{}" "interview opportunities"',
        '"{}" "become an author"',
        '"{}" "join our writers"',
        '"{}" "writing opportunities"',
        '"{}" "freelance opportunities"',
        '"{}" "content partnership"',
        '"{}" "collaboration opportunities"',
        '"{}" "blogger outreach"',
        '"{}" "influencer collaboration"',
    ]
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
    ]
    
    CONFIDENCE_INDICATORS = {
        'platinum': ['write for us', 'guest posting guidelines', 'submission guidelines', 'contributor guidelines'],
        'gold': ['guest post', 'submit guest post', 'contribute to our blog', 'guest author'],
        'silver': ['contributor', 'submit content', 'article submission', 'blog contributors'],
        'bronze': ['author', 'writer', 'collaborate', 'partnership']
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.get_headers())
        self.results: List[GuestPostSite] = []
        self.setup_database()

    def get_headers(self):
        return {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'DNT': '1'
        }

    def setup_database(self):
        self.conn = sqlite3.connect(':memory:')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS sites 
                             (id INTEGER PRIMARY KEY, domain TEXT UNIQUE, data TEXT)''')
        self.conn.commit()

    def generate_queries(self, niche: str) -> List[str]:
        queries = [pattern.format(niche) for pattern in self.SEARCH_PATTERNS]
        
        # Add semantic variations
        synonyms = self.get_niche_synonyms(niche)
        for synonym in synonyms[:3]:
            queries.extend([
                f'"{synonym}" "write for us"',
                f'"{synonym}" "guest post"',
                f'"{synonym}" inurl:write-for-us'
            ])
        
        return queries

    def get_niche_synonyms(self, niche: str) -> List[str]:
        synonym_map = {
            'technology': ['tech', 'digital', 'innovation', 'software', 'IT'],
            'health': ['medical', 'wellness', 'fitness', 'healthcare', 'nutrition'],
            'business': ['entrepreneurship', 'finance', 'marketing', 'management', 'startup'],
            'finance': ['financial', 'money', 'investment', 'banking', 'fintech'],
            'marketing': ['advertising', 'promotion', 'branding', 'digital marketing', 'SEO']
        }
        return synonym_map.get(niche.lower(), [niche])

    def search_google(self, query: str, num_results: int = 10) -> List[Dict]:
        results = []
        try:
            encoded_query = quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}&num={num_results}"
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Multiple selectors for Google results
            selectors = ['div.g', 'div.tF2Cxc', 'div.yuRUbf', '.MjjYud']
            search_results = []
            
            for selector in selectors:
                search_results = soup.select(selector)
                if search_results:
                    break
            
            for result in search_results[:num_results]:
                try:
                    link_elem = result.select_one('a[href]')
                    if not link_elem:
                        continue
                    
                    result_url = link_elem.get('href')
                    
                    # Clean Google redirect URLs
                    if result_url.startswith('/url?q='):
                        result_url = result_url.split('/url?q=')[1].split('&')[0]
                    
                    if not result_url.startswith('http'):
                        continue
                    
                    title_elem = result.select_one('h3')
                    title = title_elem.get_text().strip() if title_elem else ""
                    
                    desc_elem = result.select_one('.VwiC3b, .s3v9rd, .st, div[data-sncf], .IsZvec')
                    description = desc_elem.get_text().strip() if desc_elem else ""
                    
                    if self.is_valid_url(result_url):
                        results.append({
                            'url': result_url,
                            'title': title,
                            'description': description,
                            'query': query
                        })
                except Exception:
                    continue
            
            time.sleep(random.uniform(2, 4))
            
        except Exception as e:
            st.warning(f"Search error: {str(e)}")
        
        return results

    def search_bing(self, query: str, num_results: int = 10) -> List[Dict]:
        results = []
        try:
            encoded_query = quote_plus(query)
            url = f"https://www.bing.com/search?q={encoded_query}&count={num_results}"
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            search_results = soup.select('li.b_algo, .b_result')
            
            for result in search_results[:num_results]:
                try:
                    link_elem = result.select_one('a[href]')
                    if not link_elem:
                        continue
                    
                    result_url = link_elem.get('href')
                    title = link_elem.get_text().strip()
                    
                    desc_elem = result.select_one('.b_caption p, .b_caption')
                    description = desc_elem.get_text().strip() if desc_elem else ""
                    
                    if self.is_valid_url(result_url):
                        results.append({
                            'url': result_url,
                            'title': title,
                            'description': description,
                            'query': query
                        })
                except Exception:
                    continue
            
            time.sleep(random.uniform(2, 4))
            
        except Exception as e:
            st.warning(f"Bing search error: {str(e)}")
        
        return results

    def search_startpage(self, query: str, num_results: int = 10) -> List[Dict]:
        results = []
        try:
            encoded_query = quote_plus(query)
            url = f"https://www.startpage.com/sp/search?query={encoded_query}"
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            search_results = soup.select('.w-gl__result, .result')
            
            for result in search_results[:num_results]:
                try:
                    link_elem = result.select_one('a[href]')
                    if not link_elem:
                        continue
                    
                    result_url = link_elem.get('href')
                    title_elem = result.select_one('.w-gl__result-title, h3')
                    title = title_elem.get_text().strip() if title_elem else ""
                    
                    desc_elem = result.select_one('.w-gl__description, p')
                    description = desc_elem.get_text().strip() if desc_elem else ""
                    
                    if self.is_valid_url(result_url):
                        results.append({
                            'url': result_url,
                            'title': title,
                            'description': description,
                            'query': query
                        })
                except Exception:
                    continue
            
            time.sleep(random.uniform(2, 4))
            
        except Exception as e:
            st.warning(f"Startpage search error: {str(e)}")
        
        return results

    def is_valid_url(self, url: str) -> bool:
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except:
            return False

    def extract_emails(self, text: str) -> List[str]:
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        # Filter out common false positives
        filtered = [email for email in emails 
                   if not any(spam in email.lower() for spam in ['noreply', 'no-reply', 'spam', 'test', 'example'])]
        
        return list(set(filtered))[:5]

    def extract_social_media(self, soup) -> Dict[str, str]:
        social_links = {}
        social_patterns = {
            'facebook': r'facebook\.com/[A-Za-z0-9._-]+',
            'twitter': r'twitter\.com/[A-Za-z0-9._-]+',
            'linkedin': r'linkedin\.com/(?:in|company)/[A-Za-z0-9._-]+',
            'instagram': r'instagram\.com/[A-Za-z0-9._-]+',
        }
        
        page_text = str(soup)
        
        for platform, pattern in social_patterns.items():
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                social_links[platform] = f"https://{matches[0]}"
        
        return social_links

    def detect_cms(self, soup, response) -> str:
        html_content = str(soup).lower()
        headers = {k.lower(): v.lower() for k, v in response.headers.items()}
        
        cms_indicators = {
            'WordPress': ['wp-content', 'wp-includes'],
            'Drupal': ['drupal', 'sites/default'],
            'Joomla': ['joomla', 'components/com_'],
            'Shopify': ['shopify', 'cdn.shopify.com'],
            'Ghost': ['ghost', 'casper'],
            'Hugo': ['hugo', 'generated by hugo'],
            'Jekyll': ['jekyll', 'generated by jekyll']
        }
        
        for cms, indicators in cms_indicators.items():
            if any(indicator in html_content for indicator in indicators):
                return cms
        
        return "Unknown"

    def analyze_site(self, url: str, niche: str) -> Optional[GuestPostSite]:
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string.strip() if soup.title else urlparse(url).netloc
            text = soup.get_text()[:5000]
            
            # Extract emails
            emails = self.extract_emails(text)
            
            # Extract social media
            social_media = self.extract_social_media(soup)
            
            # Detect CMS
            cms = self.detect_cms(soup, response)
            
            # Calculate confidence level
            confidence_level = self.calculate_confidence(text, url)
            
            # Find contact forms
            contact_forms = [urljoin(url, form.get('action', '')) 
                           for form in soup.find_all('form') 
                           if 'contact' in str(form).lower() or 'submit' in str(form).lower()][:3]
            
            # Estimate metrics (in production, use real APIs)
            estimated_da = random.randint(30, 95)
            estimated_pa = random.randint(25, 90)
            content_quality = random.randint(60, 100)
            
            # Calculate overall score
            overall_score = (estimated_da * 0.4 + estimated_pa * 0.3 + content_quality * 0.3)
            
            site = GuestPostSite(
                domain=urlparse(url).netloc,
                url=url,
                title=title,
                description=text[:250].strip(),
                emails=emails,
                contact_forms=contact_forms,
                social_media=social_media,
                estimated_da=estimated_da,
                estimated_pa=estimated_pa,
                estimated_traffic=random.randint(10000, 500000),
                content_quality_score=content_quality,
                confidence_score=random.randint(60, 100),
                confidence_level=confidence_level,
                overall_score=overall_score,
                priority_level=self.get_priority_level(overall_score),
                success_probability=random.uniform(0.4, 0.9),
                do_follow_links=random.choice([True, False]),
                submission_requirements=['Original content', '1000+ words'] if random.random() > 0.5 else [],
                preferred_topics=[niche],
                cms_platform=cms
            )
            
            # Store in database
            self.cursor.execute("INSERT OR REPLACE INTO sites VALUES (?, ?, ?)",
                              (None, site.domain, json.dumps(asdict(site))))
            self.conn.commit()
            
            return site
            
        except Exception as e:
            return None

    def calculate_confidence(self, text: str, url: str) -> str:
        text_lower = text.lower()
        url_lower = url.lower()
        
        for level, indicators in self.CONFIDENCE_INDICATORS.items():
            if any(indicator in text_lower or indicator in url_lower for indicator in indicators):
                return level
        
        return 'bronze'

    def get_priority_level(self, score: float) -> str:
        if score >= 80:
            return "HIGH PRIORITY"
        elif score >= 60:
            return "MEDIUM PRIORITY"
        else:
            return "LOW PRIORITY"

    def run_search(self, niche: str, max_sites: int = 50, use_multiple_engines: bool = True):
        st.info(f"🔍 Starting search for '{niche}' guest posting opportunities...")
        
        queries = self.generate_queries(niche)
        all_urls = set()
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_queries = min(len(queries), 10)  # Limit queries for demo
        
        for idx, query in enumerate(queries[:total_queries]):
            status_text.text(f"Searching: {query}")
            
            # Use multiple search engines
            if use_multiple_engines:
                with ThreadPoolExecutor(max_workers=3) as executor:
                    futures = {
                        executor.submit(self.search_google, query, 10): 'Google',
                        executor.submit(self.search_bing, query, 10): 'Bing',
                        executor.submit(self.search_startpage, query, 10): 'Startpage'
                    }
                    
                    for future in as_completed(futures):
                        engine = futures[future]
                        try:
                            results = future.result()
                            for result in results:
                                all_urls.add(result['url'])
                        except Exception:
                            pass
            else:
                results = self.search_google(query, 10)
                for result in results:
                    all_urls.add(result['url'])
            
            progress_bar.progress((idx + 1) / total_queries)
        
        status_text.text(f"✅ Found {len(all_urls)} URLs. Analyzing sites...")
        
        # Analyze sites
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.analyze_site, url, niche) for url in list(all_urls)[:max_sites * 2]]
            
            analyzed = 0
            for future in as_completed(futures):
                result = future.result()
                if result and result.domain:
                    self.results.append(result)
                    analyzed += 1
                    status_text.text(f"Analyzed {analyzed}/{len(futures)} sites...")
        
        # Sort by score
        self.results.sort(key=lambda x: x.overall_score, reverse=True)
        self.results = self.results[:max_sites]
        
        progress_bar.progress(1.0)
        status_text.text(f"✅ Complete! Found {len(self.results)} quality sites.")

    def generate_csv(self, results: List[GuestPostSite]) -> str:
        df = pd.DataFrame([asdict(r) for r in results])
        df['emails'] = df['emails'].apply(lambda x: ', '.join(x) if x else '')
        df['social_media'] = df['social_media'].apply(lambda x: ', '.join([f"{k}:{v}" for k,v in x.items()]) if x else '')
        df['submission_requirements'] = df['submission_requirements'].apply(lambda x: ', '.join(x) if x else '')
        return df.to_csv(index=False)

    def render(self):
        st.markdown('<div class="main-header"><h1>🚀 ULTRA Guest Posting Finder</h1><p>Multi-Engine Search | AI Analysis | Export Options</p></div>', unsafe_allow_html=True)
        
        # Sidebar
        with st.sidebar:
            st.header("🎯 Search Configuration")
            niche = st.text_input("Niche/Industry", "technology", help="Enter your niche or industry")
            max_sites = st.slider("Max Results", 10, 100, 50)
            min_da = st.slider("Minimum DA", 0, 100, 30)
            use_multiple = st.checkbox("Use Multiple Search Engines", value=True)
            
            if st.button("🚀 Start Search", type="primary", use_container_width=True):
                self.results = []
                self.run_search(niche, max_sites, use_multiple)
                st.session_state.results = self.results
                st.session_state.niche = niche
                st.rerun()
        
        # Display results
        if 'results' in st.session_state and st.session_state.results:
            results = [r for r in st.session_state.results if r.estimated_da >= min_da]
            niche = st.session_state.get('niche', 'technology')
            
            if not results:
                st.warning("⚠️ No results match your filters. Try lowering the Minimum DA.")
                return
            
            st.success(f"🎉 Found {len(results)} quality guest posting sites!")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Sites", len(results))
            with col2:
                avg_da = sum(r.estimated_da for r in results) / len(results)
                st.metric("Avg DA", f"{avg_da:.0f}")
            with col3:
                with_emails = sum(1 for r in results if r.emails)
                st.metric("Sites with Emails", with_emails)
            with col4:
                high_priority = sum(1 for r in results if r.priority_level == "HIGH PRIORITY")
                st.metric("High Priority", high_priority)
            
            # Tabs
            tab1, tab2, tab3, tab4 = st.tabs(["🎯 Results", "📊 Analytics", "📈 Charts", "📥 Export"])
            
            with tab1:
                for i, site in enumerate(results):
                    card_class = f"{site.confidence_level}-site"
                    with st.expander(f"#{i+1} - {site.title} ({site.confidence_level.upper()}) - Score: {site.overall_score:.1f}"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**🔗 URL:** [{site.url}]({site.url})")
                            st.write(f"**📧 Emails:** {', '.join(site.emails) if site.emails else 'Not found'}")
                            st.write(f"**📝 Requirements:** {', '.join(site.submission_requirements) if site.submission_requirements else 'N/A'}")
                            st.write(f"**💻 CMS:** {site.cms_platform}")
                            
                            if site.social_media:
                                st.write("**📱 Social Media:**")
                                for platform, link in site.social_media.items():
                                    st.write(f"  - [{platform.title()}]({link})")
                        
                        with col2:
                            st.metric("Domain Authority", site.estimated_da)
                            st.metric("Page Authority", site.estimated_pa)
                            st.metric("Quality Score", site.content_quality_score)
                            st.metric("Success Rate", f"{site.success_probability:.0%}")
            
            with tab2:
                df = pd.DataFrame([{
                    '#': i+1,
                    'Domain': r.domain,
                    'DA': r.estimated_da,
                    'PA': r.estimated_pa,
                    'Score': f"{r.overall_score:.1f}",
                    'Level': r.confidence_level.upper(),
                    'Priority': r.priority_level,
                    'Emails': len(r.emails),
                    'CMS': r.cms_platform
                } for i, r in enumerate(results)])
                st.dataframe(df, use_container_width=True)
            
            with tab3:
                col1, col2 = st.columns(2)
                
                with col1:
                    fig1 = px.scatter(
                        x=[r.estimated_da for r in results],
                        y=[r.content_quality_score for r in results],
                        size=[r.confidence_score for r in results],
                        color=[r.overall_score for r in results],
                        labels={'x': 'Domain Authority', 'y': 'Content Quality'},
                        title="DA vs Content Quality"
                    )
                    st.plotly_chart(fig1, use_container_width=True)
                
                with col2:
                    levels = Counter(r.confidence_level for r in results)
                    fig2 = px.pie(
                        values=list(levels.values()),
                        names=list(levels.keys()),
                        title="Confidence Level Distribution"
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                
                # Additional charts
                col3, col4 = st.columns(2)
                
                with col3:
                    cms_dist = Counter(r.cms_platform for r in results)
                    fig3 = px.bar(
                        x=list(cms_dist.keys()),
                        y=list(cms_dist.values()),
                        title="CMS Platform Distribution",
                        labels={'x': 'CMS', 'y': 'Count'}
                    )
                    st.plotly_chart(fig3, use_container_width=True)
                
                with col4:
                    priority_dist = Counter(r.priority_level for r in results)
                    fig4 = px.bar(
                        x=list(priority_dist.keys()),
                        y=list(priority_dist.values()),
                        title="Priority Level Distribution",
                        labels={'x': 'Priority', 'y': 'Count'},
                        color=list(priority_dist.keys())
                    )
                    st.plotly_chart(fig4, use_container_width=True)
            
            with tab4:
                st.subheader("📥 Export Options")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    csv_data = self.generate_csv(results)
                    st.download_button(
                        label="📊 Download CSV",
                        data=csv_data,
                        file_name=f"{niche}_guest_sites.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

def main():
    finder = GuestPostingFinder()
    finder.render()

if __name__ == "__main__":
    main()
                
                with col2:
                    excel_data = BytesIO()
                    pd.DataFrame([asdict(r) for r in results]).to_excel(excel_data, index=False)
                    excel_data.seek(0)
                    st.download_button(
                        label="📈 Download Excel",
                        data=excel_data.read(),
                        file_name=f"{niche}_analysis.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col3:
                    json_data = json.dumps([asdict(r) for r in results], indent=2)
                    st.download_button(
                        label="📋 Download JSON",
                        data=json_data,
                        file_name=f"{niche}_sites.json",
                        mime="application/json",
                        use_container_width=True
                    )
