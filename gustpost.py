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
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
import random
import whois

# Attempt to import textstat for readability scores
try:
    from textstat import flesch_reading_ease
except ImportError:
    st.warning("`textstat` library not found. Readability scores will be disabled. Please run `pip install textstat`.")
    def flesch_reading_ease(text):
        return 0 # Fallback function

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
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        self.ultimate_patterns = {
            'basic_footprints': ['"{niche}" "write for us"', '"{niche}" "guest post"'],
            'advanced_footprints': ['"{niche}" inurl:write-for-us', '"{niche}" inurl:contribute'],
            'title_patterns': ['"{niche}" intitle:"write for us"', '"{niche}" intitle:"guest post"'],
            'industry_specific': ['"{niche}" "accepting guest posts"', '"{niche}" "looking for contributors"'],
        }
        self.ultimate_indicators = {
            'platinum_confidence': ['write for us', 'guest posting guidelines', 'submission guidelines'],
            'gold_confidence': ['guest post', 'submit guest post', 'guest author'],
            'silver_confidence': ['contributor', 'submit content', 'collaborate with us'],
            'bronze_confidence': ['submit', 'contribute', 'author'],
        }
        self.results = []

    def get_random_headers(self):
        return {'User-Agent': random.choice(self.user_agents)}

    def generate_ultimate_queries(self, niche, competitors=None, location=None):
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
        headers = self.get_random_headers()
        try:
            if engine == 'google':
                url = f"https://www.google.com/search?q={quote_plus(query)}&num=20&hl=en"
            elif engine == 'bing':
                url = f"https://www.bing.com/search?q={quote_plus(query)}&count=20"
            else: # duckduckgo
                url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            links = []
            
            if engine == 'google':
                for a in soup.select('div.g a[href]'):
                    if a['href'].startswith('/url?q='):
                        links.append(unquote(a['href'].split('/url?q=')[1].split('&')[0]))
                    elif a['href'].startswith('http'):
                        links.append(a['href'])
            elif engine == 'bing':
                for a in soup.select('li.b_algo h2 a'):
                    links.append(a['href'])
            else: # duckduckgo
                for a in soup.select('.result__a'):
                    links.append(a['href'])
            
            return [link for link in links if self.is_valid_url(link)]
        except requests.RequestException:
            return []

    def is_valid_url(self, url):
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                return False
            blocked_domains = ['google.com', 'youtube.com', 'facebook.com', 'twitter.com', 'wikipedia.org']
            return not any(blocked in parsed.netloc for blocked in blocked_domains)
        except:
            return False

    def get_domain_age_score(self, domain):
        try:
            domain_info = whois.whois(domain)
            creation_date = domain_info.creation_date
            if isinstance(creation_date, list):
                creation_date = creation_date[0]
            if creation_date:
                age_years = (datetime.now() - creation_date).days / 365.25
                if age_years > 10: return 15
                elif age_years > 5: return 10
                elif age_years > 2: return 5
        except Exception:
            pass
        return 2

    def analyze_website(self, url):
        try:
            headers = self.get_random_headers()
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text().lower()
            
            analysis = {
                'url': url, 'domain': urlparse(url).netloc,
                'title': soup.title.string.strip() if soup.title and soup.title.string else "No Title",
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
            
            analysis = self.calculate_all_scores(analysis, page_text)
            return analysis
        except Exception:
            return None

    def find_guest_posting_indicators(self, page_text):
        found = []
        for confidence, indicators in self.ultimate_indicators.items():
            for indicator in indicators:
                if indicator in page_text:
                    found.append({'text': indicator, 'confidence': confidence.split('_')[0]})
        return found

    def calculate_all_scores(self, analysis, page_text):
        score = sum({'platinum': 25, 'gold': 15, 'silver': 10, 'bronze': 5}.get(ind['confidence'], 0) for ind in analysis['indicators_found'])
        analysis['confidence_score'] = min(score, 100)
        
        da_score = self.get_domain_age_score(analysis['domain']) + (15 if analysis['https_enabled'] else 0) + min(analysis['external_links'] * 0.5, 20)
        da_score += (25 if any(tld in analysis['domain'] for tld in ['.edu', '.gov']) else 10)
        analysis['domain_authority'] = min(int(da_score * 1.5), 100)

        analysis['trust_score'] = min((25 if analysis['emails'] else 0) + (20 if analysis['https_enabled'] else 0) + (15 if analysis['domain_authority'] > 50 else 5), 100)
        analysis['spam_score'] = min((20 if analysis['external_links'] > 100 else 0) + (15 if analysis['word_count'] < 300 else 0) + (20 if analysis['domain_authority'] < 10 else 0), 100)

        try:
            ease = flesch_reading_ease(page_text)
            analysis['reading_ease'] = ease
            quality_score = {True: 30, 40 <= ease < 60: 20}.get(60 <= ease <= 80, 10)
        except:
            analysis['reading_ease'] = 0
            quality_score = 10
        quality_score += (20 if analysis['heading_structure']['h1'] >= 1 else 0) + (20 if analysis['word_count'] > 1500 else 10)
        analysis['content_quality_score'] = min(quality_score, 100)
        
        seo_score = (20 if analysis['title'] and 30 < len(analysis['title']) < 65 else 5) + (15 if analysis['https_enabled'] else 0)
        analysis['seo_score'] = min(seo_score, 100)

        return analysis

    def parallel_search_and_analyze(self, niche, competitors, location, max_sites):
        st.info("🚀 Initiating ULTIMATE search... This may take a few minutes.")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_queries = self.generate_ultimate_queries(niche, competitors, location)
        all_urls = set()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            search_futures = {executor.submit(self.search_engine, query, engine) for query in all_queries for engine in ['google', 'bing', 'duckduckgo']}
            for i, future in enumerate(as_completed(search_futures)):
                all_urls.update(future.result())
                progress_bar.progress(int(((i + 1) / len(search_futures)) * 50))
                status_text.text(f"🔍 Searching... Found {len(all_urls)} potential sites.")

        unique_urls = list(all_urls)[:max_sites * 2]
        status_text.text(f"🔬 Found {len(unique_urls)} unique URLs. Starting deep analysis...")
        
        results = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            analysis_futures = {executor.submit(self.analyze_website, url) for url in unique_urls}
            for i, future in enumerate(as_completed(analysis_futures)):
                result = future.result()
                if result and result.get('confidence_score', 0) > 10:
                    results.append(result)
                progress_bar.progress(50 + int(((i + 1) / len(analysis_futures)) * 50))
                status_text.text(f"🔬 Analyzing... {i+1}/{len(analysis_futures)} sites processed. Found {len(results)} opportunities.")
                if len(results) >= max_sites:
                    break
        
        results.sort(key=lambda x: (x.get('confidence_score', 0) * 0.5 + x.get('domain_authority', 0) * 0.3), reverse=True)
        status_text.success(f"✅ ULTIMATE analysis complete! Found {len(results[:max_sites])} high-quality opportunities.")
        self.results = results[:max_sites]
        return self.results

# --- UI AND DASHBOARD FUNCTIONS ---
def create_ultimate_dashboard(results):
    st.markdown("---")
    st.markdown("## 📊 ULTIMATE Analytics Dashboard")
    if not results:
        st.warning("🚫 No results to analyze!")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    avg_da = int(sum(r.get('domain_authority', 0) for r in results) / len(results)) if results else 0
    sites_with_email = len([r for r in results if r.get('emails')])
    avg_confidence = int(sum(r.get('confidence_score', 0) for r in results) / len(results)) if results else 0
    
    col1.metric("🎯 Total Sites", len(results))
    col2.metric("📈 Avg. DA", avg_da)
    col3.metric("📧 With Email", sites_with_email)
    col4.metric("💡 Avg. Confidence", f"{avg_confidence}/100")

    col1, col2 = st.columns(2)
    df = pd.DataFrame(results)
    with col1:
        fig = px.scatter(df, x='domain_authority', y='confidence_score', size='word_count', color='trust_score', hover_name='domain', title="Confidence vs. Domain Authority")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        df['confidence_level'] = df['confidence_score'].apply(lambda x: 'Platinum' if x >= 75 else 'Gold' if x >= 50 else 'Silver' if x >= 25 else 'Bronze')
        level_counts = df['confidence_level'].value_counts()
        fig = px.pie(values=level_counts.values, names=level_counts.index, title="Distribution by Confidence Level", color_discrete_map={'Platinum':'#E5E4E2','Gold':'#FFD700', 'Silver':'#C0C0C0', 'Bronze':'#CD7F32'})
        st.plotly_chart(fig, use_container_width=True)

def create_export_options(results):
    if not results: return
    st.markdown("---")
    st.markdown("### 📥 ULTIMATE Export Hub")
    df_export = pd.DataFrame(results)
    df_export['emails'] = df_export['emails'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
    df_export['indicators_found'] = df_export['indicators_found'].apply(lambda x: ', '.join([i['text'] for i in x]) if isinstance(x, list) else '')

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(label="📊 Download as CSV", data=df_export.to_csv(index=False).encode('utf-8'), file_name=f"guest_post_sites_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
    with col2:
        st.download_button(label="📋 Download as JSON", data=json.dumps(results, indent=2, default=str), file_name=f"guest_post_analysis_{datetime.now().strftime('%Y%m%d')}.json", mime="application/json")
    with col3:
        excel_buffer = BytesIO()
        df_export.to_excel(excel_buffer, index=False, sheet_name='Guest Posting Sites')
        st.download_button(label="📈 Download as Excel", data=excel_buffer.getvalue(), file_name=f"guest_post_sites_{datetime.now().strftime('%Y%m%d')}.xlsx")

# --- MAIN APPLICATION LOGIC ---
def main():
    st.markdown('<div class="main-header"><h1>🚀 ULTIMATE Guest Posting Sites Finder</h1><p>An Advanced AI-Powered Discovery System for SEO & Content Marketers</p></div>', unsafe_allow_html=True)
    
    if 'finder' not in st.session_state:
        st.session_state.finder = UltimateGuestPostingFinder()
    
    with st.sidebar:
        st.markdown("### ⚙️ ULTIMATE Configuration")
        niche = st.text_input("🎯 Your Niche/Industry", placeholder="e.g., technology, health, SaaS")
        st.markdown("#### 🔧 Advanced Options (Optional)")
        competitors = [c.strip() for c in st.text_area("🏆 Competitor Websites", placeholder="competitor1.com\ncompetitor2.com").split('\n') if c.strip()]
        location = st.text_input("🌍 Geographic Focus", placeholder="e.g., USA, UK, Canada")
        max_sites = st.slider("🎯 Maximum Sites to Find", 10, 200, 50)
        search_button = st.button("🚀 START ULTIMATE SEARCH", type="primary")
    
    if search_button:
        if not niche:
            st.error("🚫 Please enter your niche/industry to begin the search.")
        else:
            st.session_state.results = st.session_state.finder.parallel_search_and_analyze(niche, competitors, location, max_sites)
    
    if 'results' in st.session_state:
        results = st.session_state.results
        if results:
            st.markdown(f'<div class="success-card"><h3>🎉 ULTIMATE Search Complete!</h3><p>Found <strong>{len(results)}</strong> high-quality guest posting opportunities for "<strong>{niche}</strong>".</p></div>', unsafe_allow_html=True)
            
            tab1, tab2, tab3 = st.tabs(["🎯 Premium Results", "📊 Analytics Dashboard", "📥 Export Hub"])
            with tab1:
                for i, result in enumerate(results):
                    with st.expander(f"🏆 #{i+1} - {result.get('title', 'Unknown')} (DA: {result.get('domain_authority', 0)})"):
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.markdown(f"**🌐 URL:** [{result.get('domain', 'N/A')}]({result.get('url', '#')})")
                            if result.get('emails'):
                                st.markdown(f"**📧 Contact Emails:** {', '.join(result.get('emails', []))}")
                        with col2:
                            st.metric("💡 Confidence", f"{result.get('confidence_score', 0)}/100")
                            st.metric("📈 Domain Authority", f"{result.get('domain_authority', 0)}/100")
            with tab2:
                create_ultimate_dashboard(results)
            with tab3:
                create_export_options(results)
        elif search_button:
            st.markdown('<div class="warning-card"><h3>🔍 No Results Found</h3><p>Try broadening your niche or removing filters.</p></div>', unsafe_allow_html=True)
    else:
        st.info("💡 Enter your niche in the sidebar and click 'START' to discover opportunities.")

    st.markdown("<div style='text-align: center; color: #888;'><p><strong>🚀 ULTIMATE Guest Posting Finder</strong></p></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
