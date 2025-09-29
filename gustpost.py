import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import random
from urllib.parse import urlparse, quote
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="🚀 Peak Level Guest Post Finder",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .success-text { color: #00d26a; }
    .warning-text { color: #ff6b6b; }
</style>
""", unsafe_allow_html=True)

class AdvancedGuestPostFinder:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
    
    def get_random_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def advanced_search_queries(self, keyword):
        """Generate search queries"""
        queries = [
            f'"{keyword}" "write for us"',
            f'"{keyword}" "guest post"',
            f'"{keyword}" "guest article"',
            f'"{keyword}" "contribute to"',
            f'"{keyword}" "submit article"',
            f'"{keyword}" "become a contributor"',
            f'"{keyword}" "accepting guest posts"',
            f'"{keyword}" "guest blogging"',
            f'"{keyword}" "submit blog post"',
            f'intitle:"write for us" "{keyword}"',
            f'intitle:"guest post" "{keyword}"',
            f'inurl:"write-for-us" "{keyword}"',
            f'inurl:"guest-post" "{keyword}"',
            f'"{keyword}" "blogging opportunities"',
            f'"{keyword}" "content submission"',
            f'"{keyword}" "looking for writers"',
            f'"{keyword}" "contributor guidelines"',
            f'"{keyword}" "submit your article"',
            f'"{keyword}" "guest column"',
            f'"{keyword}" "guest post opportunity"',
            f'"{keyword}" "write for our blog"',
            f'"{keyword}" "accepting contributions"',
            f'"{keyword}" "blog contributor"',
        ]
        return queries
    
    def search_google_advanced(self, query):
        """Advanced Google search with multiple parsing methods"""
        try:
            search_url = f"https://www.google.com/search?q={quote(query)}&num=20"
            headers = self.get_random_headers()
            response = requests.get(search_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return []
                
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Method 1: Modern Google structure
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/url?q=' in href:
                    try:
                        # Extract actual URL from Google redirect
                        url = href.split('/url?q=')[1].split('&')[0]
                        if url.startswith('http') and 'google.com' not in url:
                            results.append(url)
                    except:
                        continue
            
            # Method 2: Alternative parsing
            for g in soup.find_all('div', class_='g'):
                anchors = g.find_all('a', href=True)
                for anchor in anchors:
                    href = anchor['href']
                    if '/url?q=' in href and 'google.com' not in href:
                        try:
                            url = href.split('/url?q=')[1].split('&')[0]
                            if url.startswith('http'):
                                results.append(url)
                        except:
                            continue
            
            # Remove duplicates and return
            return list(set(results))[:15]  # Return top 15 unique results
            
        except Exception as e:
            st.error(f"Search error: {str(e)}")
            return []
    
    def calculate_domain_score(self, url, content):
        """Calculate domain quality score"""
        score = 0
        factors = {}
        
        try:
            domain = urlparse(url).netloc.lower()
            content_lower = content.lower()
            
            # TLD Score
            tld = domain.split('.')[-1]
            if tld in ['com', 'org', 'net', 'edu', 'gov']:
                score += 15
                factors['premium_tld'] = 15
            
            # Domain Authority Indicators
            if domain.count('.') <= 2:
                score += 10
                factors['clean_domain'] = 10
            
            # Content Quality
            if len(content) > 3000:
                score += 20
                factors['rich_content'] = 20
            elif len(content) > 1000:
                score += 10
                factors['good_content'] = 10
            
            # Guest Post Signals
            guest_indicators = ['write for us', 'guest post', 'contribute', 'submit article', 'guest blogging']
            guest_count = sum(1 for indicator in guest_indicators if indicator in content_lower)
            score += guest_count * 8
            factors['guest_signals'] = guest_count * 8
            
            # Contact Information
            contact_indicators = ['contact', 'email', 'form', 'message us']
            contact_count = sum(1 for indicator in contact_indicators if indicator in content_lower)
            if contact_count >= 2:
                score += 15
                factors['contact_info'] = 15
            
            # Professional Signals
            professional_indicators = ['about us', 'team', 'services', 'blog', 'privacy policy']
            professional_count = sum(1 for indicator in professional_indicators if indicator in content_lower)
            score += professional_count * 3
            factors['professional'] = professional_count * 3
            
            # Social Signals
            social_indicators = ['twitter', 'facebook', 'linkedin', 'instagram']
            social_count = sum(1 for social in social_indicators if social in content_lower)
            score += social_count * 2
            factors['social_media'] = social_count * 2
            
            # Freshness
            current_year = str(datetime.now().year)
            if current_year in content:
                score += 10
                factors['recent'] = 10
                
        except Exception as e:
            st.error(f"Scoring error: {e}")
        
        return min(100, score), factors
    
    def get_site_content(self, url):
        """Get website content with error handling"""
        try:
            response = requests.get(url, headers=self.get_random_headers(), timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove scripts and styles
                for script in soup(["script", "style"]):
                    script.decompose()
                
                title = soup.title.string if soup.title else "No Title"
                text = soup.get_text()
                
                # Clean up text
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                return title, text
            return "No Title", ""
        except:
            return "No Title", ""
    
    def extract_emails(self, text):
        """Extract email addresses from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return list(set(emails))[:3]  # Return max 3 unique emails

def main():
    st.markdown('<h1 class="main-header">🚀 Peak Level Guest Post Finder</h1>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'search_done' not in st.session_state:
        st.session_state.search_done = False
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'all_urls_found' not in st.session_state:
        st.session_state.all_urls_found = []
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Advanced Settings")
        
        keyword = st.text_input("🎯 Main Keyword/Niche", 
                               placeholder="e.g., digital marketing, health, technology",
                               value="health")
        
        st.subheader("🔍 Search Intensity")
        search_depth = st.slider("Number of Queries", 5, 30, 15, 
                                help="Higher = more results but slower")
        
        st.subheader("🎯 Target Filters")
        min_domain_score = st.slider("Minimum Domain Score", 10, 80, 25,
                                    help="Higher score = better quality sites")
        include_contact_info = st.checkbox("Extract Contact Info", True)
        
        if st.button("🚀 Start Advanced Search", type="primary", use_container_width=True):
            if keyword.strip():
                perform_advanced_search(keyword, search_depth, min_domain_score, include_contact_info)
            else:
                st.error("❌ Please enter a keyword!")
    
    # Main content
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Search Engines", "Google")
    with col2:
        st.metric("Search Queries", f"{search_depth}+")
    with col3:
        st.metric("Analysis Factors", "10+")
    
    st.info("💡 **Tip:** Start with popular niches like 'health', 'technology', or 'digital marketing' for best results.")
    
    # Display results
    if st.session_state.search_done:
        display_search_results(keyword, min_domain_score)

def perform_advanced_search(keyword, search_depth, min_domain_score, include_contact_info):
    """Perform the search operation"""
    finder = AdvancedGuestPostFinder()
    
    # Setup progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Step 1: Generate queries
    status_text.text("🔄 Generating search queries...")
    queries = finder.advanced_search_queries(keyword)[:search_depth]
    
    # Step 2: Search across queries
    status_text.text("🔍 Searching Google...")
    all_urls = []
    
    for i, query in enumerate(queries):
        progress_bar.progress((i + 1) / len(queries) * 0.4)
        urls = finder.search_google_advanced(query)
        all_urls.extend(urls)
        time.sleep(1)  # Be respectful
    
    # Remove duplicates
    unique_urls = list(set(all_urls))
    
    # Step 3: Analyze sites
    status_text.text("📊 Analyzing website quality...")
    results = []
    
    for i, url in enumerate(unique_urls[:25]):  # Analyze top 25 sites
        progress = 0.4 + (i + 1) / min(25, len(unique_urls)) * 0.6
        progress_bar.progress(progress)
        
        try:
            title, content = finder.get_site_content(url)
            score, factors = finder.calculate_domain_score(url, content)
            
            if score >= min_domain_score:
                result_data = {
                    'URL': url,
                    'Title': title,
                    'Domain Score': score,
                    'Factors': str(factors)
                }
                
                if include_contact_info:
                    emails = finder.extract_emails(content)
                    result_data['Emails'] = ', '.join(emails) if emails else 'Not found'
                
                results.append(result_data)
            
            time.sleep(0.5)  # Be respectful
            
        except Exception as e:
            continue
    
    # Update session state
    st.session_state.search_results = results
    st.session_state.all_urls_found = unique_urls
    st.session_state.search_done = True
    st.session_state.current_keyword = keyword
    
    progress_bar.progress(100)
    status_text.text("✅ Search complete!")

def display_search_results(keyword, min_domain_score):
    """Display the search results"""
    results = st.session_state.search_results
    all_urls = st.session_state.all_urls_found
    
    if results:
        # Create DataFrame
        df = pd.DataFrame(results)
        df = df.sort_values('Domain Score', ascending=False)
        
        st.success(f"🎉 Found {len(results)} high-quality sites for '{keyword}'!")
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Sites Analyzed", len(all_urls))
        with col2:
            st.metric("Quality Sites", len(results))
        with col3:
            avg_score = df['Domain Score'].mean()
            st.metric("Avg Quality Score", f"{avg_score:.1f}")
        with col4:
            best_score = df['Domain Score'].max()
            st.metric("Best Score", f"{best_score:.1f}")
        
        # Results table
        st.subheader("📋 High-Quality Guest Posting Sites")
        
        # Create a nicer display
        for idx, row in df.iterrows():
            with st.expander(f"🏆 Score: {row['Domain Score']} | {row['Title'][:60]}..."):
                st.write(f"**URL:** [{row['URL']}]({row['URL']})")
                st.write(f"**Full Title:** {row['Title']}")
                st.write(f"**Quality Factors:** {row['Factors']}")
                if 'Emails' in row:
                    st.write(f"**Contact Emails:** {row['Emails']}")
        
        # Download option
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name=f"guest_posts_{keyword}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            type="primary"
        )
        
    else:
        st.warning(f"❌ No sites found with minimum score of {min_domain_score} for '{keyword}'")
        
        if all_urls:
            st.info(f"🔍 Found {len(all_urls)} sites but they didn't meet quality criteria.")
            st.write("**Try these adjustments:**")
            st.write("- Lower the Minimum Domain Score to 15-20")
            st.write("- Try different keywords")
            st.write("- Increase Number of Queries")
            
            with st.expander("View found URLs (low quality)"):
                for url in all_urls[:15]:
                    st.write(f"• {url}")

if __name__ == "__main__":
    main()
