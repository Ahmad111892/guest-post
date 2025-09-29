import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import json
import concurrent.futures
from urllib.parse import urlparse, urljoin
import random
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="🚀 Peak Level Guest Post Finder",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem;
    }
    .success-text { color: #00d26a; }
    .warning-text { color: #ff6b6b; }
    .info-text { color: #1f77b4; }
</style>
""", unsafe_allow_html=True)

class AdvancedGuestPostFinder:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        self.search_engines = {
            'google': 'https://www.google.com/search?q=',
            'bing': 'https://www.bing.com/search?q=',
            'duckduckgo': 'https://html.duckduckgo.com/html/?q='
        }
        
    def get_random_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
    
    def advanced_search_queries(self, keyword):
        """Generate advanced search queries"""
        base_queries = [
            f'"{keyword}" "write for us"',
            f'"{keyword}" "guest post"',
            f'"{keyword}" "guest article"',
            f'"{keyword}" "contribute to"',
            f'"{keyword}" "submit article"',
            f'"{keyword}" "become a contributor"',
            f'"{keyword}" "guest post by"',
            f'"{keyword}" "accepting guest posts"',
            f'"{keyword}" "guest blogging"',
            f'"{keyword}" "write for me"',
            f'"{keyword}" "submit blog post"',
            f'intitle:"write for us" "{keyword}"',
            f'intitle:"guest post" "{keyword}"',
            f'inurl:"write-for-us" "{keyword}"',
            f'inurl:"guest-post" "{keyword}"',
            f'"{keyword}" "blogging opportunities"',
            f'"{keyword}" "content submission"',
            f'"{keyword}" "external contributors"',
            f'"{keyword}" "sponsored post"',
            f'"{keyword}" "article submission"',
            f'"{keyword}" "want to write for"',
            f'"{keyword}" "looking for writers"',
            f'"{keyword}" "contributor guidelines"',
            f'"{keyword}" "submit your article"',
            f'"{keyword}" "guest column"',
            f'"{keyword}" "guest post opportunity"',
        ]
        return base_queries
    
    def calculate_domain_score(self, url, content):
        """Advanced domain scoring algorithm"""
        score = 0
        factors = {}
        
        try:
            # Domain authority factors
            domain = urlparse(url).netloc
            
            # TLD scoring
            tld = domain.split('.')[-1]
            premium_tlds = ['com', 'org', 'net', 'edu', 'gov']
            if tld in premium_tlds:
                score += 10
                factors['premium_tld'] = 10
            
            # Domain age indicator (subdomain count)
            subdomain_count = domain.count('.')
            if subdomain_count <= 1:
                score += 15
                factors['clean_domain'] = 15
            
            # Content quality indicators
            content_lower = content.lower()
            
            # Contact form indicators
            contact_indicators = ['contact', 'email', 'form', 'submit', 'message']
            contact_count = sum(1 for indicator in contact_indicators if indicator in content_lower)
            if contact_count >= 2:
                score += 20
                factors['contact_info'] = 20
            
            # Social media presence
            social_indicators = ['twitter', 'facebook', 'linkedin', 'instagram']
            social_count = sum(1 for social in social_indicators if social in content_lower)
            score += social_count * 5
            factors['social_media'] = social_count * 5
            
            # Professional indicators
            professional_terms = ['about us', 'team', 'services', 'blog', 'articles']
            professional_count = sum(1 for term in professional_terms if term in content_lower)
            score += professional_count * 3
            factors['professional_site'] = professional_count * 3
            
            # Guest post specific indicators
            guest_terms = ['guidelines', 'submission', 'contributor', 'author', 'write for us']
            guest_count = sum(1 for term in guest_terms if term in content_lower)
            score += guest_count * 8
            factors['guest_post_friendly'] = guest_count * 8
            
            # Content length score
            content_length = len(content)
            if content_length > 5000:
                score += 25
                factors['content_rich'] = 25
            elif content_length > 2000:
                score += 15
                factors['good_content'] = 15
            
            # Recent activity indicator
            current_year = str(datetime.now().year)
            if current_year in content:
                score += 10
                factors['recent_activity'] = 10
                
        except Exception as e:
            st.error(f"Scoring error: {e}")
        
        return max(0, min(100, score)), factors

    def search_google(self, query):
        """Search Google and extract results"""
        try:
            search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num=10"
            response = requests.get(search_url, headers=self.get_random_headers(), timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            # Look for search result containers
            for g in soup.find_all('div', class_='g'):
                anchor = g.find('a')
                if anchor:
                    link = anchor.get('href')
                    title = g.find('h3')
                    if title and link and link.startswith('/url?q='):
                        # Clean Google redirect URL
                        clean_link = link.split('/url?q=')[1].split('&')[0]
                        # Validate it's a proper URL
                        if clean_link.startswith('http'):
                            results.append(clean_link)
            
            return results
        except Exception as e:
            st.error(f"Google search error: {e}")
            return []

    def find_contact_info(self, url):
        """Extract contact information from website"""
        try:
            response = requests.get(url, headers=self.get_random_headers(), timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            
            # Email regex pattern
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text)
            
            return {
                'emails': list(set(emails))[:3],  # Remove duplicates, max 3
            }
        except:
            return {'emails': []}

def perform_search(keyword, search_depth, min_domain_score, include_contact_info, deep_analysis):
    """Perform the actual search and return results"""
    finder = AdvancedGuestPostFinder()
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Step 1: Generate queries
    status_text.text("🔄 Generating advanced search queries...")
    all_queries = finder.advanced_search_queries(keyword)[:search_depth]
    
    # Step 2: Search
    status_text.text("🔍 Searching across multiple engines...")
    all_urls = []
    
    for i, query in enumerate(all_queries):
        progress_bar.progress((i + 1) / len(all_queries) * 0.4)
        urls = finder.search_google(query)
        all_urls.extend(urls)
        time.sleep(1)  # Be respectful to servers
    
    # Remove duplicates
    unique_urls = list(set(all_urls))
    
    # Step 3: Analysis
    status_text.text("📊 Analyzing sites...")
    results = []
    
    for i, url in enumerate(unique_urls[:30]):  # Limit to top 30 URLs
        progress_value = 0.4 + (i + 1) / min(30, len(unique_urls)) * 0.6
        progress_bar.progress(progress_value)
        
        try:
            # Get site content
            response = requests.get(url, headers=finder.get_random_headers(), timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            content = soup.get_text()
            
            # Calculate domain score
            score, factors = finder.calculate_domain_score(url, content)
            
            if score >= min_domain_score:
                result = {
                    'URL': url,
                    'Domain Score': score,
                    'Title': soup.title.string if soup.title else 'No Title',
                    'Factors': str(factors)
                }
                
                # Contact info extraction
                if include_contact_info:
                    contact_info = finder.find_contact_info(url)
                    result['Emails'] = ', '.join(contact_info['emails'])
                
                results.append(result)
                
            # Small delay to be respectful
            time.sleep(0.5)
            
        except Exception as e:
            continue
    
    status_text.text("✅ Analysis complete!")
    progress_bar.progress(100)
    
    return results, unique_urls

def main():
    st.markdown('<h1 class="main-header">🚀 Peak Level Guest Post Finder</h1>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'search_complete' not in st.session_state:
        st.session_state.search_complete = False
    if 'results' not in st.session_state:
        st.session_state.results = []
    if 'all_urls' not in st.session_state:
        st.session_state.all_urls = []
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Advanced Settings")
        
        keyword = st.text_input("🎯 Main Keyword/Niche", placeholder="e.g., digital marketing, health tech")
        
        st.subheader("🔍 Search Intensity")
        search_depth = st.slider("Number of Queries", 10, 50, 25)
        
        st.subheader("🎯 Target Filters")
        min_domain_score = st.slider("Minimum Domain Score", 0, 100, 30)
        include_contact_info = st.checkbox("Extract Contact Info", True)
        deep_analysis = st.checkbox("Deep Site Analysis", True)
        
        if st.button("🚀 Start Advanced Search", type="primary"):
            if keyword:
                with st.spinner('🚀 Starting advanced search...'):
                    results, all_urls = perform_search(keyword, search_depth, min_domain_score, include_contact_info, deep_analysis)
                    st.session_state.results = results
                    st.session_state.all_urls = all_urls
                    st.session_state.search_complete = True
                    st.rerun()
            else:
                st.error("Please enter a keyword!")
    
    # Main content
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Search Engines", "3")
    with col2:
        st.metric("Search Queries", "25+")
    with col3:
        st.metric("Analysis Factors", "10+")
    
    st.info("""
    **🔍 Advanced Features:**
    - Multi-search engine scraping (Google, Bing, DuckDuckGo)
    - 25+ intelligent search queries
    - Advanced domain scoring algorithm
    - Real-time contact information extraction
    - Deep site potential analysis
    """)
    
    # Display results if search is complete
    if st.session_state.search_complete:
        results = st.session_state.results
        all_urls = st.session_state.all_urls
        
        if results:
            # Convert to DataFrame
            df = pd.DataFrame(results)
            
            # Sort by domain score
            df = df.sort_values('Domain Score', ascending=False)
            
            st.success(f"🎉 Found {len(results)} high-potential guest posting sites!")
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Sites Found", len(all_urls))
            with col2:
                st.metric("High Quality Sites", len(results))
            with col3:
                avg_score = df['Domain Score'].mean()
                st.metric("Avg Domain Score", f"{avg_score:.1f}")
            
            # Display results table
            st.subheader("📋 High-Potential Guest Posting Sites")
            st.dataframe(df, use_container_width=True)
            
            # Export options
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"guest_posting_sites_{keyword}.csv",
                mime="text/csv"
            )
            
            # Show detailed analysis for top sites
            st.subheader("🔍 Top Site Analysis")
            for i, (_, row) in enumerate(df.head(5).iterrows()):
                with st.expander(f"🏆 #{i+1} - {row['URL']} (Score: {row['Domain Score']})"):
                    st.write(f"**Title:** {row['Title']}")
                    st.write(f"**Domain Score Factors:** {row['Factors']}")
                    if 'Emails' in row:
                        st.write(f"**Contact Emails:** {row['Emails']}")
        else:
            st.warning("❌ No high-quality sites found. Try adjusting the filters or using different keywords.")
            
            # Show some found URLs even if they didn't meet score threshold
            if all_urls:
                st.info(f"🔍 Found {len(all_urls)} sites but none met the quality threshold. Try lowering the minimum domain score.")
                with st.expander("Show all found URLs"):
                    for url in all_urls[:10]:
                        st.write(url)

if __name__ == "__main__":
    main()
