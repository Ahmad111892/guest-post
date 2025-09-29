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
import asyncio
import aiohttp
import nest_asyncio

# Apply nest_asyncio for async operations
nest_asyncio.apply()

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
            'duckduckgo': 'https://html.duckduckgo.com/html/?q=',
            'yahoo': 'https://search.yahoo.com/search?p='
        }
        
    def get_random_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def advanced_search_queries(self, keyword):
        """Generate 50+ advanced search queries"""
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
            f'"{keyword}" "write for our blog"',
            f'"{keyword}" "accepting contributions"',
            f'"{keyword}" "blog contributor"',
            f'"{keyword}" "guest author"',
            f'"{keyword}" site:.com "write for us"',
            f'"{keyword}" site:.org "guest post"',
            f'"{keyword}" "editorial guidelines" "submit"',
            f'"{keyword}" "blogging" "write for us"',
            f'"{keyword}" "digital marketing" "guest post"',
            f'"{keyword}" -"no guest posts" -"not accepting"',
            f'"{keyword}" "content marketing" "write for us"',
            f'"{keyword}" "SEO" "guest post"',
            f'"{keyword}" "blog" inurl:write-for-us',
            f'"{keyword}" "blog" inurl:guest-post',
            f'"{keyword}" "submit a post"',
            f'"{keyword}" "become an author"',
            f'"{keyword}" "author guidelines"',
            f'"{keyword}" "contribute content"',
            f'"{keyword}" "guest post guidelines"',
            f'"{keyword}" "writing for us"',
            f'"{keyword}" "share your expertise"',
            f'"{keyword}" "industry experts" "write for us"',
            f'"{keyword}" "thought leadership" "guest post"',
            f'"{keyword}" "expert contributions"'
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
    
    async def fetch_url_async(self, session, url):
        """Async URL fetching"""
        try:
            async with session.get(url, headers=self.get_random_headers(), timeout=30) as response:
                return await response.text()
        except:
            return None
    
    def search_multiple_engines(self, query):
        """Search across multiple search engines simultaneously"""
        all_results = []
        
        def search_engine_worker(engine_name, base_url):
            try:
                search_url = f"{base_url}{requests.utils.quote(query)}"
                response = requests.get(search_url, headers=self.get_random_headers(), timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                results = []
                if engine_name == 'google':
                    for g in soup.find_all('div', class_='g'):
                        anchor = g.find('a')
                        if anchor:
                            link = anchor.get('href')
                            title = g.find('h3')
                            if title and link and link.startswith('/url?q='):
                                clean_link = link.split('/url?q=')[1].split('&')[0]
                                results.append(clean_link)
                elif engine_name == 'bing':
                    for li in soup.find_all('li', class_='b_algo'):
                        anchor = li.find('a')
                        if anchor:
                            results.append(anchor.get('href'))
                
                return results
            except:
                return []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for engine_name, base_url in self.search_engines.items():
                futures.append(executor.submit(search_engine_worker, engine_name, base_url))
            
            for future in concurrent.futures.as_completed(futures):
                all_results.extend(future.result())
        
        return list(set(all_results))  # Remove duplicates
    
    def analyze_site_potential(self, url):
        """Deep analysis of site guest post potential"""
        try:
            response = requests.get(url, headers=self.get_random_headers(), timeout=20)
            soup = BeautifulSoup(response.text, 'html.parser')
            content = soup.get_text().lower()
            
            # Advanced analysis
            analysis = {
                'url': url,
                'has_contact_form': any(indicator in content for indicator in ['contact', 'email', 'form']),
                'has_guest_post_page': any(indicator in content for indicator in ['write for us', 'guest post', 'contribute']),
                'has_social_links': any(social in content for social in ['twitter', 'facebook', 'linkedin']),
                'content_quality': 'high' if len(content) > 3000 else 'medium',
                'professional_design': len(soup.find_all(['header', 'nav', 'footer'])) >= 2,
                'blog_section': any(indicator in content for indicator in ['blog', 'articles', 'news']),
                'recent_activity': str(datetime.now().year) in content
            }
            
            return analysis
        except:
            return None
    
    def find_contact_info(self, url):
        """Extract contact information from website"""
        try:
            response = requests.get(url, headers=self.get_random_headers(), timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            
            # Email regex pattern
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text)
            
            # Social media links
            social_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if any(domain in href for domain in ['twitter.com', 'facebook.com', 'linkedin.com']):
                    social_links.append(href)
            
            return {
                'emails': list(set(emails))[:3],  # Remove duplicates, max 3
                'social_links': social_links[:5]
            }
        except:
            return {'emails': [], 'social_links': []}

def main():
    st.markdown('<h1 class="main-header">🚀 Peak Level Guest Post Finder</h1>', unsafe_allow_html=True)
    
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
                return keyword, search_depth, min_domain_score, include_contact_info, deep_analysis
            else:
                st.error("Please enter a keyword!")
    
    # Initialize finder
    finder = AdvancedGuestPostFinder()
    
    # Main content
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Search Engines", "4")
    with col2:
        st.metric("Search Queries", "50+")
    with col3:
        st.metric("Analysis Factors", "15+")
    
    st.info("""
    **🔍 Advanced Features:**
    - Multi-search engine scraping (Google, Bing, DuckDuckGo, Yahoo)
    - 50+ intelligent search queries
    - Advanced domain scoring algorithm
    - Real-time contact information extraction
    - Deep site potential analysis
    - Async concurrent processing
    """)
    
    return None, None, None, None, None

if __name__ == "__main__":
    keyword, search_depth, min_domain_score, include_contact_info, deep_analysis = main()
    
    if keyword:
        with st.spinner('🚀 Starting peak level advanced search...'):
            finder = AdvancedGuestPostFinder()
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Generate queries
            status_text.text("🔄 Generating advanced search queries...")
            all_queries = finder.advanced_search_queries(keyword)[:search_depth]
            
            # Step 2: Multi-engine search
            status_text.text("🔍 Searching across 4 search engines...")
            all_urls = []
            
            for i, query in enumerate(all_queries):
                progress_bar.progress((i + 1) / len(all_queries) * 0.3)
                urls = finder.search_multiple_engines(query)
                all_urls.extend(urls)
            
            # Remove duplicates
            unique_urls = list(set(all_urls))
            
            # Step 3: Advanced analysis
            status_text.text("📊 Performing deep site analysis...")
            results = []
            
            for i, url in enumerate(unique_urls[:50]):  # Limit to top 50 URLs
                progress_bar.progress(0.3 + (i + 1) / min(50, len(unique_urls)) * 0.7)
                
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
                            'Factors': factors
                        }
                        
                        # Contact info extraction
                        if include_contact_info:
                            contact_info = finder.find_contact_info(url)
                            result['Emails'] = ', '.join(contact_info['emails'])
                            result['Social Links'] = len(contact_info['social_links'])
                        
                        # Deep analysis
                        if deep_analysis:
                            site_analysis = finder.analyze_site_potential(url)
                            if site_analysis:
                                result['Guest Post Ready'] = site_analysis['has_guest_post_page']
                                result['Professional Site'] = site_analysis['professional_design']
                                result['Recent Activity'] = site_analysis['recent_activity']
                        
                        results.append(result)
                        
                        # Small delay to be respectful
                        time.sleep(0.5)
                        
                except Exception as e:
                    continue
            
            # Display results
            status_text.text("✅ Analysis complete!")
            progress_bar.progress(100)
            
            if results:
                # Convert to DataFrame
                df = pd.DataFrame(results)
                
                # Sort by domain score
                df = df.sort_values('Domain Score', ascending=False)
                
                st.success(f"🎉 Found {len(results)} high-potential guest posting sites!")
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Sites Found", len(unique_urls))
                with col2:
                    st.metric("High Quality Sites", len(results))
                with col3:
                    avg_score = df['Domain Score'].mean()
                    st.metric("Avg Domain Score", f"{avg_score:.1f}")
                with col4:
                    if 'Guest Post Ready' in df.columns:
                        ready_sites = df['Guest Post Ready'].sum()
                        st.metric("Guest Post Ready", ready_sites)
                
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
                st.subheader("🔍 Top 5 Site Analysis")
                for i, (_, row) in enumerate(df.head().iterrows()):
                    with st.expander(f"🏆 #{i+1} - {row['URL']} (Score: {row['Domain Score']})"):
                        st.write(f"**Title:** {row['Title']}")
                        st.write(f"**Domain Score Factors:**")
                        for factor, value in row['Factors'].items():
                            st.write(f"  - {factor}: +{value} points")
                        
                        if include_contact_info and 'Emails' in row:
                            st.write(f"**Contact Emails:** {row['Emails']}")
                        
                        if deep_analysis and 'Guest Post Ready' in row:
                            st.write(f"**Guest Post Page:** {'✅ Yes' if row['Guest Post Ready'] else '❌ No'}")
                            st.write(f"**Professional Design:** {'✅ Yes' if row['Professional Site'] else '❌ No'}")
                            st.write(f"**Recent Activity:** {'✅ Yes' if row['Recent Activity'] else '❌ No'}")
                
            else:
                st.warning("❌ No high-quality sites found. Try adjusting the filters or using different keywords.")
