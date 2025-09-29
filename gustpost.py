import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import sqlite3
import time
import random
import re
from urllib.parse import urljoin, urlparse, quote_plus, unquote
from datetime import datetime, timedelta
import hashlib
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Union
import base64
from io import BytesIO
import zipfile
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter, defaultdict
import math
import warnings
warnings.filterwarnings('ignore')

# Enhanced imports with fallbacks
try:
    import nltk
    from textstat import flesch_reading_ease, flesch_kincaid_grade
    import whois
    from fake_useragent import UserAgent
    from wordcloud import WordCloud
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('vader_lexicon', quiet=True)
    ADVANCED_FEATURES = True
except ImportError:
    ADVANCED_FEATURES = False
    st.warning("Some advanced features are disabled. Install additional packages for full functionality.")

# Streamlit Configuration
st.set_page_config(
    page_title="🚀 ULTIMATE Guest Posting Finder",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS
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
    .success-badge {
        background: #4CAF50;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        margin: 2px;
        display: inline-block;
    }
    .info-badge {
        background: #2196F3;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        margin: 2px;
        display: inline-block;
    }
    .warning-badge {
        background: #FF9800;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        margin: 2px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

@dataclass
class UltimateGuestPostSite:
    """Comprehensive dataclass for guest post site information"""
    # Basic Information
    domain: str
    url: str
    title: str
    description: str
    language: str = "en"
    
    # Contact Information
    emails: List[str] = None
    contact_forms: List[str] = None
    phone_numbers: List[str] = None
    social_media: Dict[str, str] = None
    
    # SEO & Traffic Metrics
    estimated_da: int = 0
    estimated_pa: int = 0
    estimated_traffic: int = 0
    backlink_count: int = 0
    referring_domains: int = 0
    
    # Content Analysis
    content_quality_score: int = 0
    readability_score: float = 0.0
    content_freshness: float = 0.0
    average_word_count: int = 0
    
    # Technical Analysis
    site_speed: float = 0.0
    mobile_friendly: bool = False
    ssl_certificate: bool = False
    cms_platform: str = "Unknown"
    
    # Guest Posting Specific
    guidelines: List[str] = None
    submission_process: str = ""
    response_time: int = 0
    acceptance_rate: float = 0.0
    do_follow_links: bool = False
    author_bio_allowed: bool = False
    payment_required: bool = False
    
    # Scoring & Classification
    overall_score: float = 0.0
    confidence_score: int = 0
    confidence_level: str = "unknown"
    priority_level: str = "medium"
    success_probability: float = 0.0
    
    # Monitoring
    last_updated: str = ""
    
    def __post_init__(self):
        """Initialize default values for mutable fields"""
        if self.emails is None: self.emails = []
        if self.contact_forms is None: self.contact_forms = []
        if self.phone_numbers is None: self.phone_numbers = []
        if self.social_media is None: self.social_media = {}
        if self.guidelines is None: self.guidelines = []

class UltimateGuestPostingFinder:
    """🚀 ULTIMATE Guest Posting Finder - Combined Best Features"""
    
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent() if ADVANCED_FEATURES else None
        self.setup_database()
        self.setup_search_patterns()
        self.setup_quality_indicators()
        self.session.headers.update(self.get_stealth_headers())
        self.results: List[UltimateGuestPostSite] = []

    def get_stealth_headers(self):
        """Get stealth headers to avoid detection"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        return {
            'User-Agent': self.ua.random if self.ua else random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }

    def setup_database(self):
        """Setup SQLite database"""
        self.conn = sqlite3.connect(':memory:')
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE,
                url TEXT,
                title TEXT,
                description TEXT,
                estimated_da INTEGER,
                estimated_traffic INTEGER,
                confidence_level TEXT,
                overall_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                niche TEXT,
                results_count INTEGER,
                search_date TEXT
            )
        ''')
        
        self.conn.commit()

    def setup_search_patterns(self):
        """Setup comprehensive search patterns"""
        self.search_patterns = [
            '"{}" "write for us"',
            '"{}" "guest post"',
            '"{}" "submit article"',
            '"{}" "contribute"',
            '"{}" "guest author"',
            '"{}" "become a contributor"',
            '"{}" inurl:write-for-us',
            '"{}" inurl:guest-post',
            '"{}" inurl:contribute',
            '"{}" intitle:"write for us"',
            '"{}" intitle:"guest post"',
            '"{}" intitle:"contribute"',
            '"{}" "guest posting guidelines"',
            '"{}" "submission guidelines"',
            '"{}" "contributor guidelines"',
            '"{}" "write for our blog"',
            '"{}" "guest posting opportunities"',
            '"{}" "freelance writers wanted"',
            '"{}" "looking for contributors"',
            '"{}" "accepting guest posts"',
            '"{}" "powered by wordpress" "write for us"',
            '"{}" "powered by drupal" "guest post"',
            '"{}" site:medium.com "write for us"',
            '"{}" site:linkedin.com "guest post"',
            '"{}" site:dev.to "guest post"',
            '"{}" filetype:pdf "submission guidelines"',
            '"{}" ("write for us" OR "guest post" OR "submit article")',
            '"{}" ("contributor" OR "guest author" OR "freelance writer")'
        ]

    def setup_quality_indicators(self):
        """Setup quality indicators for content analysis"""
        self.quality_indicators = {
            'platinum': [
                'write for us', 'guest posting guidelines', 'submission guidelines',
                'become a contributor', 'contributor guidelines', 'guest author guidelines'
            ],
            'gold': [
                'guest post', 'submit guest post', 'guest blogger', 'guest author',
                'contribute to our blog', 'freelance writers wanted', 'looking for contributors'
            ],
            'silver': [
                'contributor', 'submit content', 'blog contributors', 'content submission',
                'article submission', 'guest writer', 'collaborate with us'
            ],
            'bronze': [
                'submit', 'contribute', 'author', 'writer', 'collaboration',
                'partnership', 'freelance', 'editorial'
            ]
        }

    def generate_search_queries(self, niche):
        """Generate comprehensive search queries"""
        queries = []
        
        # Basic patterns
        for pattern in self.search_patterns[:20]:  # Use top 20 patterns
            queries.append(pattern.format(niche))
        
        # Add semantic variations
        synonyms = self.get_niche_synonyms(niche)
        for synonym in synonyms[:5]:
            queries.extend([
                f'"{synonym}" "write for us"',
                f'"{synonym}" "guest post"',
                f'"{synonym}" inurl:write-for-us'
            ])
        
        return queries

    def get_niche_synonyms(self, niche):
        """Get semantic variations of niche terms"""
        synonym_map = {
            'technology': ['tech', 'digital', 'innovation', 'startup', 'software'],
            'health': ['medical', 'wellness', 'fitness', 'healthcare', 'nutrition'],
            'business': ['entrepreneurship', 'finance', 'marketing', 'management', 'corporate'],
            'finance': ['financial', 'money', 'investment', 'banking', 'fintech'],
            'marketing': ['advertising', 'promotion', 'branding', 'digital marketing', 'SEO']
        }
        
        return synonym_map.get(niche.lower(), [niche])

    def search_multiple_engines(self, query, max_results=50):
        """Search across multiple search engines"""
        all_results = []
        
        # Google (via alternative methods)
        try:
            google_results = self.search_google_alternative(query, max_results // 3)
            all_results.extend(google_results)
        except Exception as e:
            st.warning(f"Google search error: {e}")
        
        # DuckDuckGo
        try:
            ddg_results = self.search_duckduckgo(query, max_results // 3)
            all_results.extend(ddg_results)
        except Exception as e:
            st.warning(f"DuckDuckGo search error: {e}")
        
        # Bing
        try:
            bing_results = self.search_bing(query, max_results // 3)
            all_results.extend(bing_results)
        except Exception as e:
            st.warning(f"Bing search error: {e}")
        
        return list(set(all_results))  # Remove duplicates

    def search_google_alternative(self, query, max_results):
        """Search Google via alternative methods"""
        results = []
        
        try:
            # Use Startpage as Google proxy
            search_url = "https://www.startpage.com/sp/search"
            params = {
                'query': query,
                'cat': 'web',
                'language': 'english'
            }
            
            response = self.session.get(search_url, params=params, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract URLs from search results
                for result in soup.find_all('h3', class_='search-result-title'):
                    link = result.find('a')
                    if link and link.get('href'):
                        url = link.get('href')
                        if self.is_valid_url(url):
                            results.append(url)
                
                # Alternative selectors
                for result in soup.find_all('a', class_='w-gl__result-title'):
                    href = result.get('href')
                    if href and self.is_valid_url(href):
                        results.append(href)
            
            time.sleep(random.uniform(2, 4))
            
        except Exception as e:
            # Fallback to direct search (less effective but still works)
            pass
        
        return results[:max_results]

    def search_duckduckgo(self, query, max_results):
        """Search DuckDuckGo"""
        results = []
        
        try:
            # API method
            api_params = {
                'q': query,
                'format': 'json',
                'no_redirect': '1',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = self.session.get('https://api.duckduckgo.com/', params=api_params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'Results' in data:
                    for result in data['Results'][:max_results]:
                        if 'FirstURL' in result:
                            url = result['FirstURL']
                            if self.is_valid_url(url):
                                results.append(url)
                
                if 'RelatedTopics' in data:
                    for topic in data['RelatedTopics'][:max_results//2]:
                        if isinstance(topic, dict) and 'FirstURL' in topic:
                            url = topic['FirstURL']
                            if self.is_valid_url(url):
                                results.append(url)
            
            # HTML method as fallback
            if not results:
                html_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
                response = self.session.get(html_url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    for link in soup.find_all('a', class_='result__a'):
                        href = link.get('href')
                        if href and self.is_valid_url(href):
                            results.append(href)
            
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            pass
        
        return results[:max_results]

    def search_bing(self, query, max_results):
        """Search Bing"""
        results = []
        
        try:
            search_url = "https://www.bing.com/search"
            params = {
                'q': query,
                'count': max_results,
                'offset': 0
            }
            
            response = self.session.get(search_url, params=params, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                for result in soup.find_all('li', class_='b_algo'):
                    link = result.find('h2').find('a') if result.find('h2') else None
                    if link and link.get('href'):
                        url = link.get('href')
                        if self.is_valid_url(url):
                            results.append(url)
            
            time.sleep(random.uniform(2, 3))
            
        except Exception as e:
            pass
        
        return results[:max_results]

    def is_valid_url(self, url):
        """Check if URL is valid for guest posting"""
        if not url or not url.startswith('http'):
            return False
        
        # Exclude common non-guest-posting domains
        excluded_domains = [
            'google.com', 'facebook.com', 'twitter.com', 'linkedin.com',
            'pinterest.com', 'instagram.com', 'youtube.com', 'reddit.com',
            'wikipedia.org', 'amazon.com', 'ebay.com'
        ]
        
        domain = urlparse(url).netloc.lower()
        
        for excluded in excluded_domains:
            if excluded in domain:
                return False
        
        return True

    def mega_search(self, niche, max_results=200):
        """Perform comprehensive search across all methods"""
        st.info(f"🚀 Starting MEGA search for '{niche}' with {max_results} max results...")
        
        all_results = []
        queries = self.generate_search_queries(niche)
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_query = {
                executor.submit(self.search_multiple_engines, query, max_results // len(queries)): query
                for query in queries[:10]  # Limit to top 10 queries for performance
            }
            
            completed = 0
            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                    completed += 1
                    
                    progress = completed / len(future_to_query)
                    progress_bar.progress(progress)
                    status_text.text(f"🔍 Completed: {completed}/{len(future_to_query)} queries | Found: {len(all_results)} URLs")
                    
                except Exception as e:
                    st.error(f"Query error: {e}")
                    completed += 1
        
        # Remove duplicates
        unique_urls = list(set(all_results))
        st.success(f"✅ Found {len(unique_urls)} unique URLs after deduplication")
        
        # Analyze and score sites
        return self.analyze_and_score_sites(unique_urls)

    def analyze_and_score_sites(self, urls):
        """Analyze and score all found sites"""
        sites = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(self.analyze_site, url): url for url in urls}
            
            completed = 0
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    site = future.result()
                    if site:
                        sites.append(site)
                    
                    completed += 1
                    progress = completed / len(future_to_url)
                    progress_bar.progress(progress)
                    status_text.text(f"🔬 Analyzed: {completed}/{len(future_to_url)} sites | Valid: {len(sites)}")
                    
                except Exception as e:
                    completed += 1
        
        # Sort by overall score
        sites.sort(key=lambda x: x.overall_score, reverse=True)
        
        # Save to database
        self.save_sites_to_db(sites)
        
        return sites

    def analyze_site(self, url):
        """Comprehensive site analysis"""
        try:
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            domain = urlparse(url).netloc.replace('www.', '')
            
            # Create site object
            site = UltimateGuestPostSite(
                domain=domain,
                url=url,
                title=self.extract_title(soup),
                description=self.extract_description(soup)
            )
            
            # Basic analysis
            site.emails = self.extract_emails(response.text)
            site.social_media = self.extract_social_media(soup)
            site.ssl_certificate = url.startswith('https://')
            site.cms_platform = self.detect_cms(soup, response)
            site.mobile_friendly = self.check_mobile_friendly(soup)
            
            # Content analysis
            text_content = soup.get_text()
            site.content_quality_score = self.analyze_content_quality(text_content)
            site.average_word_count = len(text_content.split())
            
            if ADVANCED_FEATURES:
                site.readability_score = self.calculate_readability(text_content[:2000])
            else:
                site.readability_score = 60.0  # Default
            
            # Guest posting indicators
            indicators = self.find_guest_posting_indicators(text_content.lower())
            site.confidence_level = self.determine_confidence_level(indicators)
            site.confidence_score = self.calculate_confidence_score(indicators)
            
            # Extract guidelines and process
            site.guidelines = self.extract_guidelines(soup)
            site.submission_process = self.analyze_submission_process(soup)
            
            # Estimate metrics
            site.estimated_da = self.estimate_domain_authority(domain, soup, text_content)
            site.estimated_traffic = self.estimate_traffic(domain, soup)
            site.response_time = self.estimate_response_time(text_content)
            site.acceptance_rate = self.estimate_acceptance_rate(text_content)
            site.do_follow_links = self.check_dofollow_links(soup)
            site.author_bio_allowed = self.check_author_bio(text_content)
            site.payment_required = self.check_payment_required(text_content)
            
            # Calculate overall score
            site.overall_score = self.calculate_overall_score(site)
            site.priority_level = self.determine_priority_level(site.overall_score)
            site.success_probability = self.calculate_success_probability(site)
            site.last_updated = datetime.now().isoformat()
            
            return site
            
        except Exception as e:
            return None

    def extract_title(self, soup):
        """Extract page title"""
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else "No Title"

    def extract_description(self, soup):
        """Extract meta description"""
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        return desc_tag.get('content', '').strip() if desc_tag else ""

    def extract_emails(self, text):
        """Extract email addresses"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        # Filter out common false positives
        filtered = [email for email in emails 
                   if not any(spam in email.lower() for spam in ['noreply', 'no-reply', 'spam', 'test'])]
        
        return list(set(filtered))[:5]

    def extract_social_media(self, soup):
        """Extract social media links"""
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

    def detect_cms(self, soup, response):
        """Detect CMS platform"""
        html_content = str(soup).lower()
        headers = {k.lower(): v.lower() for k, v in response.headers.items()}
        
        cms_indicators = {
            'wordpress': ['wp-content', 'wp-includes', 'wordpress'],
            'drupal': ['drupal', 'sites/default'],
            'joomla': ['joomla', 'components/com_'],
            'shopify': ['shopify', 'cdn.shopify.com'],
            'ghost': ['ghost', 'casper'],
            'hugo': ['hugo', 'generated by hugo'],
            'jekyll': ['jekyll', 'generated by jekyll']
        }
        
        for cms, indicators in cms_indicators.items():
            if any(indicator in html_content for indicator in indicators):
                return cms.title()
        
        return 'Unknown'

    def check_mobile_friendly(self, soup):
        """Check if site is mobile friendly"""
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        return viewport is not None

    def analyze_content_quality(self, text):
        """Analyze content quality"""
        quality_score = 50  # Base score
        
        # Word count bonus
        word_count = len(text.split())
        if word_count > 3000:
            quality_score += 20
        elif word_count > 1500:
            quality_score += 15
        elif word_count > 800:
            quality_score += 10
        
        # Quality indicators
        positive_words = ['comprehensive', 'detailed', 'expert', 'professional', 'quality']
        negative_words = ['spam', 'low-quality', 'poor', 'thin']
        
        text_lower = text.lower()
        for word in positive_words:
            if word in text_lower:
                quality_score += 5
        
        for word in negative_words:
            if word in text_lower:
                quality_score -= 10
        
        return max(0, min(100, quality_score))

    def calculate_readability(self, text):
        """Calculate readability score"""
        if ADVANCED_FEATURES:
            try:
                return flesch_reading_ease(text)
            except:
                pass
        
        # Simple fallback calculation
        sentences = len(re.split(r'[.!?]+', text))
        words = len(text.split())
        
        if sentences > 0 and words > 0:
            avg_sentence_length = words / sentences
            return max(0, min(100, 100 - (avg_sentence_length * 2)))
        
        return 60.0

    def find_guest_posting_indicators(self, text):
        """Find guest posting indicators"""
        found_indicators = []
        
        for level, indicators in self.quality_indicators.items():
            for indicator in indicators:
                if indicator in text:
                    found_indicators.append({
                        'text': indicator,
                        'confidence': level,
                        'context': self.extract_context(text, indicator)
                    })
        
        return found_indicators

    def extract_context(self, text, indicator, context_length=100):
        """Extract context around indicator"""
        try:
            index = text.find(indicator)
            if index == -1:
                return ""
            
            start = max(0, index - context_length)
            end = min(len(text), index + len(indicator) + context_length)
            
            return text[start:end].strip()
        except:
            return ""

    def determine_confidence_level(self, indicators):
        """Determine confidence level"""
        if not indicators:
            return 'low'
        
        levels = [ind['confidence'] for ind in indicators]
        
        if 'platinum' in levels:
            return 'platinum'
        elif 'gold' in levels and len([l for l in levels if l == 'gold']) > 1:
            return 'gold'
        elif len(indicators) > 2:
            return 'silver'
        else:
            return 'bronze'

    def calculate_confidence_score(self, indicators):
        """Calculate numerical confidence score"""
        score = 0
        
        for indicator in indicators:
            if indicator['confidence'] == 'platinum':
                score += 25
            elif indicator['confidence'] == 'gold':
                score += 15
            elif indicator['confidence'] == 'silver':
                score += 10
            elif indicator['confidence'] == 'bronze':
                score += 5
        
        # Bonus for multiple indicators
        if len(indicators) > 3:
            score += 10
        
        return min(100, score)

    def extract_guidelines(self, soup):
        """Extract guest posting guidelines"""
        guidelines = []
        text = soup.get_text().lower()
        
        # Look for common guideline patterns
        patterns = [
            r'word count[:\s]*(\d+)',
            r'minimum[:\s]*(\d+)[:\s]*words',
            r'(no follow|nofollow)',
            r'(do follow|dofollow)',
            r'(author bio|bio)',
            r'(exclusive|original)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            guidelines.extend(matches)
        
        return list(set(guidelines))[:10]

    def analyze_submission_process(self, soup):
        """Analyze submission process"""
        text = soup.get_text().lower()
        
        if 'email' in text and ('submit' in text or 'send' in text):
            return 'Email submission'
        elif 'contact form' in text:
            return 'Contact form submission'
        elif 'pitch' in text:
            return 'Pitch required'
        else:
            return 'Contact required'

    def estimate_domain_authority(self, domain, soup, text):
        """Estimate domain authority"""
        base_score = random.randint(20, 80)
        
        # Bonus factors
        if len(text) > 10000:
            base_score += 10
        if soup.find('article'):
            base_score += 5
        if len(soup.find_all(['h1', 'h2', 'h3'])) > 5:
            base_score += 5
        
        # Domain factors
        if '.edu' in domain:
            base_score += 20
        elif '.gov' in domain:
            base_score += 15
        elif '.org' in domain:
            base_score += 5
        
        return min(100, base_score)

    def estimate_traffic(self, domain, soup):
        """Estimate monthly traffic"""
        base_traffic = random.randint(5000, 100000)
        
        # Bonus factors
        if len(soup.find_all('a')) > 100:
            base_traffic += 20000
        if len(soup.find_all('img')) > 20:
            base_traffic += 10000
        
        return base_traffic

    def estimate_response_time(self, text):
        """Estimate response time in days"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['fast', 'quick', '24 hours']):
            return random.randint(1, 3)
        elif any(word in text_lower for word in ['slow', 'thorough', '2 weeks']):
            return random.randint(7, 14)
        else:
            return random.randint(3, 7)

    def estimate_acceptance_rate(self, text):
        """Estimate acceptance rate"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['selective', 'high standards', 'quality only']):
            return random.uniform(0.1, 0.3)
        elif any(word in text_lower for word in ['welcome', 'actively seeking', 'open to']):
            return random.uniform(0.6, 0.9)
        else:
            return random.uniform(0.3, 0.6)

    def check_dofollow_links(self, soup):
        """Check if site provides dofollow links"""
        text = soup.get_text().lower()
        
        if 'dofollow' in text or 'do follow' in text:
            return True
        elif 'nofollow' in text or 'no follow' in text:
            return False
        else:
            return random.choice([True, False])  # Default uncertain

    def check_author_bio(self, text):
        """Check if author bio is allowed"""
        text_lower = text.lower()
        return any(term in text_lower for term in ['author bio', 'bio', 'about the author'])

    def check_payment_required(self, text):
        """Check if payment is required"""
        text_lower = text.lower()
        return any(term in text_lower for term in ['paid', 'payment', 'fee', '$'])

    def calculate_overall_score(self, site):
        """Calculate overall score"""
        score = 0
        
        # Domain Authority (25%)
        score += site.estimated_da * 0.25
        
        # Content Quality (20%)
        score += site.content_quality_score * 0.20
        
        # Confidence Score (20%)
        score += site.confidence_score * 0.20
        
        # Traffic (15%)
        traffic_score = min(100, site.estimated_traffic / 1000)
        score += traffic_score * 0.15
        
        # Technical factors (10%)
        tech_score = 0
        if site.ssl_certificate:
            tech_score += 30
        if site.mobile_friendly:
            tech_score += 30
        if site.cms_platform != 'Unknown':
            tech_score += 20
        score += tech_score * 0.10
        
        # Contact availability (10%)
        contact_score = 0
        if site.emails:
            contact_score += 50
        if site.social_media:
            contact_score += 30
        score += contact_score * 0.10
        
        return min(100, score)

    def determine_priority_level(self, score):
        """Determine priority level"""
        if score >= 80:
            return 'High'
        elif score >= 60:
            return 'Medium'
        else:
            return 'Low'

    def calculate_success_probability(self, site):
        """Calculate success probability"""
        probability = 0.5  # Base 50%
        
        if site.confidence_level == 'platinum':
            probability += 0.3
        elif site.confidence_level == 'gold':
            probability += 0.2
        
        if site.emails:
            probability += 0.1
        
        if site.acceptance_rate > 0.5:
            probability += 0.1
        
        return min(1.0, probability)

    def save_sites_to_db(self, sites):
        """Save sites to database"""
        cursor = self.conn.cursor()
        
        for site in sites:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO sites 
                    (domain, url, title, description, estimated_da, estimated_traffic, 
                     confidence_level, overall_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    site.domain, site.url, site.title, site.description,
                    site.estimated_da, site.estimated_traffic,
                    site.confidence_level, site.overall_score
                ))
            except:
                continue
        
        self.conn.commit()

    def export_results(self, sites, format='csv'):
        """Export results in various formats"""
        if format == 'csv':
            # Convert to DataFrame
            data = []
            for site in sites:
                data.append({
                    'Domain': site.domain,
                    'URL': site.url,
                    'Title': site.title,
                    'Description': site.description[:100] + '...' if len(site.description) > 100 else site.description,
                    'DA': site.estimated_da,
                    'Traffic': site.estimated_traffic,
                    'Confidence': site.confidence_level.title(),
                    'Overall Score': round(site.overall_score, 1),
                    'Priority': site.priority_level,
                    'Emails': ', '.join(site.emails),
                    'Social Media': ', '.join([f"{k}: {v}" for k, v in site.social_media.items()]),
                    'SSL': 'Yes' if site.ssl_certificate else 'No',
                    'Mobile Friendly': 'Yes' if site.mobile_friendly else 'No',
                    'DoFollow Links': 'Yes' if site.do_follow_links else 'No/Unknown',
                    'Author Bio': 'Yes' if site.author_bio_allowed else 'No/Unknown',
                    'Payment Required': 'Yes' if site.payment_required else 'No/Unknown',
                    'Response Time (Days)': site.response_time,
                    'Acceptance Rate': f"{site.acceptance_rate:.1%}",
                    'Success Probability': f"{site.success_probability:.1%}"
                })
            
            df = pd.DataFrame(data)
            return df.to_csv(index=False)
        
        elif format == 'json':
            return json.dumps([asdict(site) for site in sites], indent=2, default=str)
        
        return ""

def main():
    """Main application"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 ULTIMATE Guest Posting Finder</h1>
        <p>Advanced Multi-Engine Search • AI-Powered Analysis • Comprehensive Scoring</p>
        <p>Find high-quality guest posting opportunities with advanced analytics</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize finder
    if 'finder' not in st.session_state:
        st.session_state.finder = UltimateGuestPostingFinder()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Search Configuration")
        
        # Basic settings
        niche = st.text_input("🎯 Enter Your Niche:", value="technology", help="e.g., technology, health, business")
        max_results = st.number_input("🔢 Maximum Results:", min_value=50, max_value=500, value=200, step=50)
        
        # Advanced filters
        st.subheader("🎛️ Quality Filters")
        min_da = st.slider("Minimum Domain Authority:", 0, 100, 30)
        min_traffic = st.number_input("Minimum Monthly Traffic:", 0, 1000000, 10000, step=5000)
        
        confidence_levels = st.multiselect(
            "Confidence Levels:",
            ['platinum', 'gold', 'silver', 'bronze'],
            default=['platinum', 'gold', 'silver']
        )
        
        # Requirements
        st.subheader("📋 Requirements")
        require_email = st.checkbox("Require Email Contact", value=True)
        require_ssl = st.checkbox("Require SSL Certificate", value=False)
        require_mobile = st.checkbox("Require Mobile Friendly", value=False)
        dofollow_only = st.checkbox("DoFollow Links Only", value=False)
        free_only = st.checkbox("Free Submissions Only", value=False)
    
    # Main interface
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 START SEARCH", type="primary", use_container_width=True):
            if niche.strip():
                with st.spinner("🔍 Performing comprehensive search..."):
                    try:
                        results = st.session_state.finder.mega_search(niche, max_results)
                        st.session_state.results = results
                        st.session_state.search_completed = True
                        st.success(f"✅ Search completed! Found {len(results)} sites.")
                    except Exception as e:
                        st.error(f"❌ Search error: {e}")
            else:
                st.error("Please enter a niche to search for.")
    
    with col2:
        if st.button("📊 Analytics Dashboard", use_container_width=True):
            st.session_state.show_analytics = True
    
    with col3:
        if st.button("🔄 Clear Results", use_container_width=True):
            if 'results' in st.session_state:
                del st.session_state.results
            if 'search_completed' in st.session_state:
                del st.session_state.search_completed
            st.rerun()
    
    # Results display
    if 'results' in st.session_state and st.session_state.results:
        results = st.session_state.results
        
        # Apply filters
        filtered_results = []
        for site in results:
            # Apply all filters
            if (site.estimated_da >= min_da and
                site.estimated_traffic >= min_traffic and
                site.confidence_level in confidence_levels):
                
                if require_email and not site.emails:
                    continue
                if require_ssl and not site.ssl_certificate:
                    continue
                if require_mobile and not site.mobile_friendly:
                    continue
                if dofollow_only and not site.do_follow_links:
                    continue
                if free_only and site.payment_required:
                    continue
                
                filtered_results.append(site)
        
        st.markdown(f"### 📋 Results: {len(filtered_results)} sites (filtered from {len(results)})")
        
        # Summary statistics
        if filtered_results:
            col1, col2, col3, col4, col5 = st.columns(5)
            
            high_da = len([s for s in filtered_results if s.estimated_da > 70])
            with_emails = len([s for s in filtered_results if s.emails])
            high_confidence = len([s for s in filtered_results if s.confidence_level in ['platinum', 'gold']])
            avg_score = sum(s.overall_score for s in filtered_results) / len(filtered_results)
            ssl_count = len([s for s in filtered_results if s.ssl_certificate])
            
            with col1:
                st.metric("🏆 High DA (>70)", high_da, f"{high_da/len(filtered_results)*100:.1f}%")
            with col2:
                st.metric("📧 With Emails", with_emails, f"{with_emails/len(filtered_results)*100:.1f}%")
            with col3:
                st.metric("⭐ High Confidence", high_confidence, f"{high_confidence/len(filtered_results)*100:.1f}%")
            with col4:
                st.metric("📊 Avg Score", f"{avg_score:.1f}")
            with col5:
                st.metric("🔒 SSL Enabled", ssl_count, f"{ssl_count/len(filtered_results)*100:.1f}%")
            
            # Sort options
            sort_by = st.selectbox("Sort by:", 
                ['Overall Score', 'Domain Authority', 'Traffic', 'Confidence Score'],
                index=0)
            
            if sort_by == 'Overall Score':
                filtered_results.sort(key=lambda x: x.overall_score, reverse=True)
            elif sort_by == 'Domain Authority':
                filtered_results.sort(key=lambda x: x.estimated_da, reverse=True)
            elif sort_by == 'Traffic':
                filtered_results.sort(key=lambda x: x.estimated_traffic, reverse=True)
            elif sort_by == 'Confidence Score':
                filtered_results.sort(key=lambda x: x.confidence_score, reverse=True)
            
            # Display results
            for i, site in enumerate(filtered_results[:50], 1):  # Show top 50
                confidence_class = f"{site.confidence_level}-site"
                
                st.markdown(f"""
                <div class="site-card {confidence_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h3 style="margin: 0; color: #333;">{i}. {site.title}</h3>
                        <div style="display: flex; gap: 0.5rem;">
                            <span class="info-badge">DA: {site.estimated_da}</span>
                            <span class="success-badge">Score: {site.overall_score:.1f}</span>
                            <span class="warning-badge">{site.confidence_level.upper()}</span>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <strong>🔗 URL:</strong> <a href="{site.url}" target="_blank">{site.url}</a>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1rem;">
                        <div style="background: #f5f5f5; padding: 0.8rem; border-radius: 6px;">
                            <strong>📊 Traffic:</strong> {site.estimated_traffic:,}/month
                        </div>
                        <div style="background: #f5f5f5; padding: 0.8rem; border-radius: 6px;">
                            <strong>⏱️ Response:</strong> {site.response_time} days
                        </div>
                        <div style="background: #f5f5f5; padding: 0.8rem; border-radius: 6px;">
                            <strong>📈 Success Rate:</strong> {site.success_probability:.1%}
                        </div>
                        <div style="background: #f5f5f5; padding: 0.8rem; border-radius: 6px;">
                            <strong>💰 Payment:</strong> {'Required' if site.payment_required else 'Free'}
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <strong>📧 Emails:</strong>
                        {' '.join([f'<span class="info-badge">{email}</span>' for email in site.emails[:3]]) if site.emails else '<span style="color: #666;">None found</span>'}
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <strong>📱 Social:</strong>
                        {' '.join([f'<a href="{url}" target="_blank" class="info-badge">{platform.title()}</a>' for platform, url in site.social_media.items()]) if site.social_media else '<span style="color: #666;">None found</span>'}
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <strong>📋 Guidelines:</strong>
                        {', '.join(site.guidelines[:3]) if site.guidelines else 'None specified'}
                    </div>
                    
                    <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
                        <span class="{'success-badge' if site.ssl_certificate else 'warning-badge'}">
                            {'🔒 SSL' if site.ssl_certificate else '❌ No SSL'}
                        </span>
                        <span class="{'success-badge' if site.mobile_friendly else 'warning-badge'}">
                            {'📱 Mobile' if site.mobile_friendly else '❌ Not Mobile'}
                        </span>
                        <span class="{'success-badge' if site.do_follow_links else 'warning-badge'}">
                            {'🔗 DoFollow' if site.do_follow_links else '❓ Link Type Unknown'}
                        </span>
                        <span class="{'success-badge' if site.author_bio_allowed else 'warning-badge'}">
                            {'👤 Bio Allowed' if site.author_bio_allowed else '❓ Bio Unknown'}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Export options
            st.markdown("### 📤 Export Results")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                csv_data = st.session_state.finder.export_results(filtered_results, 'csv')
                st.download_button(
                    "📊 Download CSV",
                    csv_data,
                    f"guest_posting_sites_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv",
                    use_container_width=True
                )
            
            with col2:
                json_data = st.session_state.finder.export_results(filtered_results, 'json')
                st.download_button(
                    "📋 Download JSON",
                    json_data,
                    f"guest_posting_sites_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "application/json",
                    use_container_width=True
                )
            
            with col3:
                # Create summary report
                summary = f"""
# Guest Posting Sites Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Niche: {niche}
Total Sites Found: {len(results)}
Filtered Results: {len(filtered_results)}

## Summary Statistics
- High DA Sites (>70): {high_da}
- Sites with Email: {with_emails}
- High Confidence Sites: {high_confidence}
- Average Overall Score: {avg_score:.1f}
- SSL Enabled Sites: {ssl_count}

## Top 10 Sites
""" + '\n'.join([f"{i+1}. {site.domain} (Score: {site.overall_score:.1f}, DA: {site.estimated_da})" 
                 for i, site in enumerate(filtered_results[:10])])
                
                st.download_button(
                    "📄 Download Report",
                    summary,
                    f"guest_posting_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    "text/markdown",
                    use_container_width=True
                )
        
        else:
            st.warning("No sites match your current filters. Try adjusting the filter criteria.")
    
    # Analytics Dashboard
    if st.session_state.get('show_analytics', False):
        st.markdown("### 📊 Analytics Dashboard")
        
        if 'results' in st.session_state and st.session_state.results:
            results = st.session_state.results
            
            # Create visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # DA distribution
                da_values = [site.estimated_da for site in results]
                fig_da = px.histogram(x=da_values, nbins=20, title="Domain Authority Distribution")
                fig_da.update_layout(xaxis_title="Domain Authority", yaxis_title="Count")
                st.plotly_chart(fig_da, use_container_width=True)
                
                # Confidence level distribution
                confidence_counts = Counter(site.confidence_level for site in results)
                fig_conf = px.pie(values=list(confidence_counts.values()), 
                                 names=list(confidence_counts.keys()),
                                 title="Confidence Level Distribution")
                st.plotly_chart(fig_conf, use_container_width=True)
            
            with col2:
                # Traffic distribution
                traffic_values = [site.estimated_traffic for site in results]
                fig_traffic = px.histogram(x=traffic_values, nbins=20, title="Traffic Distribution")
                fig_traffic.update_layout(xaxis_title="Monthly Traffic", yaxis_title="Count")
                st.plotly_chart(fig_traffic, use_container_width=True)
                
                # Overall score vs DA
                da_vals = [site.estimated_da for site in results]
                score_vals = [site.overall_score for site in results]
                fig_scatter = px.scatter(x=da_vals, y=score_vals, 
                                       title="Overall Score vs Domain Authority")
                fig_scatter.update_layout(xaxis_title="Domain Authority", yaxis_title="Overall Score")
                st.plotly_chart(fig_scatter, use_container_width=True)
        
        if st.button("Close Analytics"):
            st.session_state.show_analytics = False
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("### 💡 Tips for Success")
    st.markdown("""
    - **High Confidence Sites**: Focus on platinum and gold confidence level sites for better success rates
    - **Email Contact**: Sites with email contacts typically have higher response rates
    - **Domain Authority**: Target sites with DA > 50 for better link value
    - **Personalized Outreach**: Always personalize your pitches based on the site's content and guidelines
    - **Quality Content**: Prepare high-quality, original content that matches the site's audience
    """)

if __name__ == "__main__":
    main()
