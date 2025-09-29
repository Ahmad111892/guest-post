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
    page_title="🚀 REAL SEARCH Guest Post Finder",
    page_icon="🔍",
    layout="wide"
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
    }
    .site-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

class RealSearchFinder:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
    
    def get_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
        }
    
    def generate_search_queries(self, keyword):
        """Generate multiple search queries"""
        base_keyword = keyword.lower().strip()
        queries = [
            f'"{base_keyword}" "write for us"',
            f'"{base_keyword}" "guest post"',
            f'"{base_keyword}" "guest article"',
            f'"{base_keyword}" "submit article"',
            f'"{base_keyword}" "become a contributor"',
            f'"{base_keyword}" "accepting guest posts"',
            f'"{base_keyword}" "guest blogging"',
            f'"{base_keyword}" "contribute to our blog"',
            f'"{base_keyword}" "submit guest post"',
            f'"{base_keyword}" "looking for writers"',
            f'"{base_keyword}" "blog contributor"',
            f'"{base_keyword}" "author guidelines"',
            f'intitle:"write for us" "{base_keyword}"',
            f'intitle:"guest post" "{base_keyword}"',
            f'inurl:"write-for-us" "{base_keyword}"',
            f'inurl:"guest-post" "{base_keyword}"',
            f'inurl:"contribute" "{base_keyword}"',
            f'"{base_keyword}" site:.com "write for us"',
            f'"{base_keyword}" site:.org "guest post"',
        ]
        return queries
    
    def search_duckduckgo(self, query):
        """Search using DuckDuckGo - More reliable"""
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
            response = requests.get(url, headers=self.get_headers(), timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = []
                
                # Find all result links
                for link in soup.find_all('a', class_='result__url'):
                    href = link.get('href')
                    if href and href.startswith('http'):
                        results.append(href)
                
                # Alternative parsing method
                if not results:
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if href.startswith('http') and 'duckduckgo.com' not in href:
                            results.append(href)
                
                return list(set(results))[:10]  # Remove duplicates, return top 10
            return []
        except Exception as e:
            st.error(f"Search error: {str(e)}")
            return []
    
    def search_bing(self, query):
        """Search using Bing as backup"""
        try:
            url = f"https://www.bing.com/search?q={quote(query)}"
            response = requests.get(url, headers=self.get_headers(), timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = []
                
                # Bing result parsing
                for li in soup.find_all('li', class_='b_algo'):
                    link = li.find('a')
                    if link and link.get('href'):
                        results.append(link['href'])
                
                return results[:10]
            return []
        except:
            return []
    
    def search_google_alternative(self, query):
        """Alternative Google search method"""
        try:
            url = f"https://www.google.com/search?q={quote(query)}"
            response = requests.get(url, headers=self.get_headers(), timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = []
                
                # Multiple parsing strategies for Google
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if '/url?q=' in href:
                        try:
                            actual_url = href.split('/url?q=')[1].split('&')[0]
                            if actual_url.startswith('http'):
                                results.append(actual_url)
                        except:
                            continue
                
                return list(set(results))[:10]
            return []
        except:
            return []
    
    def analyze_website(self, url):
        """Analyze a single website for guest posting potential"""
        try:
            # First, check if website is accessible
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get basic info
            title = soup.title.string if soup.title else "No Title"
            page_text = soup.get_text().lower()
            
            # Check for guest posting indicators
            guest_indicators = [
                'write for us', 'guest post', 'submit article', 'become a contributor',
                'guest blogging', 'contribute', 'submit guest post', 'author guidelines',
                'submission guidelines', 'looking for writers', 'blog contributor'
            ]
            
            found_indicators = []
            for indicator in guest_indicators:
                if indicator in page_text:
                    found_indicators.append(indicator)
            
            # Check for contact information
            contact_indicators = ['contact', 'email', 'write to us', 'get in touch']
            contact_found = any(indicator in page_text for indicator in contact_indicators)
            
            # Extract emails
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, response.text)
            emails = list(set(emails))[:3]  # Remove duplicates, max 3
            
            # Calculate quality score
            score = 0
            score += len(found_indicators) * 15
            score += len(emails) * 20
            score += 25 if contact_found else 0
            score += 20 if len(page_text) > 1000 else 0  # Content richness
            
            # Only return if it has guest posting potential
            if score >= 20:  # Minimum threshold
                return {
                    'url': url,
                    'title': title[:150],
                    'guest_indicators': found_indicators,
                    'emails': emails,
                    'contact_found': contact_found,
                    'quality_score': min(score, 100),
                    'content_length': len(page_text),
                    'status': 'Active'
                }
            
            return None
            
        except Exception as e:
            return None
    
    def perform_real_search(self, keyword, max_results=30):
        """Perform actual web search"""
        st.info("🚀 Starting REAL web search... This may take 1-2 minutes.")
        
        # Generate search queries
        queries = self.generate_search_queries(keyword)
        
        # Collect URLs from multiple search engines
        all_urls = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Search phase
        status_text.text("🔍 Searching across multiple engines...")
        for i, query in enumerate(queries):
            progress_bar.progress((i + 1) / len(queries) * 0.3)
            
            # Try DuckDuckGo first
            ddg_results = self.search_duckduckgo(query)
            all_urls.extend(ddg_results)
            
            # Try Bing as backup
            if len(ddg_results) < 5:
                bing_results = self.search_bing(query)
                all_urls.extend(bing_results)
            
            # Small delay to be respectful
            time.sleep(2)
        
        # Remove duplicates
        unique_urls = list(set(all_urls))
        status_text.text(f"📊 Found {len(unique_urls)} unique URLs. Analyzing websites...")
        
        # Analysis phase
        results = []
        for i, url in enumerate(unique_urls[:max_results]):
            progress = 0.3 + (i + 1) / min(max_results, len(unique_urls)) * 0.7
            progress_bar.progress(progress)
            
            analysis = self.analyze_website(url)
            if analysis:
                results.append(analysis)
            
            # Be respectful to servers
            time.sleep(1)
        
        progress_bar.progress(1.0)
        return results

def main():
    st.markdown("""
    <div class="main-header">
        <h1>🚀 REAL SEARCH Guest Post Finder</h1>
        <p>100% Real Web Search • No Demo Data • Actual Results</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'search_complete' not in st.session_state:
        st.session_state.search_complete = False
    if 'real_results' not in st.session_state:
        st.session_state.real_results = []
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Search Settings")
        
        keyword = st.text_input(
            "🎯 Enter Your Niche/Keyword", 
            value="digital marketing",
            placeholder="e.g., technology, health, business, finance"
        )
        
        st.info("💡 **Tips for better results:**")
        st.write("- Use specific niches")
        st.write("- Be patient (search takes 1-2 minutes)")
        st.write("- Try different keywords if needed")
        
        if st.button("🚀 START REAL SEARCH", type="primary", use_container_width=True):
            if keyword.strip():
                with st.spinner('🔄 Starting real web search...'):
                    finder = RealSearchFinder()
                    results = finder.perform_real_search(keyword)
                    
                    st.session_state.real_results = results
                    st.session_state.search_complete = True
                    st.session_state.current_keyword = keyword
                    st.rerun()
            else:
                st.error("❌ Please enter a keyword!")
    
    # Main content
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Search Engines", "DuckDuckGo + Bing")
    with col2:
        st.metric("Search Method", "Real-time")
    with col3:
        st.metric("Data Source", "Live Web")
    
    # Display instructions
    if not st.session_state.search_complete:
        st.info("""
        **📋 How this works:**
        1. Enter your niche/keyword
        2. Click "START REAL SEARCH" 
        3. Wait 1-2 minutes for real web search
        4. Get actual guest posting sites from live web
        
        **🔍 Searching:** DuckDuckGo + Bing
        **⏰ Time:** 1-2 minutes
        **✅ Results:** 100% Real websites
        """)
    
    # Display results
    if st.session_state.search_complete:
        display_real_results()

def display_real_results():
    """Display real search results"""
    results = st.session_state.real_results
    keyword = st.session_state.current_keyword
    
    if results:
        st.success(f"🎉 Found {len(results)} REAL guest posting sites for '{keyword}'!")
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Sites", len(results))
        with col2:
            high_quality = len([r for r in results if r['quality_score'] >= 60])
            st.metric("High Quality", high_quality)
        with col3:
            with_emails = len([r for r in results if r['emails']])
            st.metric("With Emails", with_emails)
        with col4:
            avg_score = sum(r['quality_score'] for r in results) / len(results)
            st.metric("Avg Quality", f"{avg_score:.1f}")
        
        # Display results
        st.subheader("📋 Real Guest Posting Opportunities")
        
        for i, site in enumerate(results):
            with st.expander(f"#{i+1} - Score: {site['quality_score']} - {site['title'][:60]}...", expanded=i<3):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**🌐 Website:** [{site['url']}]({site['url']})")
                    st.write(f"**📝 Title:** {site['title']}")
                    
                    if site['emails']:
                        st.write(f"**📧 Contact Emails:** {', '.join(site['emails'])}")
                    else:
                        st.write("**📧 Contact Emails:** Not found (check website contact page)")
                    
                    if site['guest_indicators']:
                        st.write(f"**🎯 Guest Post Signals:** {', '.join(site['guest_indicators'][:5])}")
                    
                    st.write(f"**📊 Content Length:** {site['content_length']} characters")
                
                with col2:
                    score_color = "🟢" if site['quality_score'] >= 70 else "🟡" if site['quality_score'] >= 50 else "🟠"
                    st.write(f"**{score_color} Quality Score:** {site['quality_score']}/100")
                    st.write(f"**✅ Contact Page:** {'Yes' if site['contact_found'] else 'Not Found'}")
                    st.write(f"**📈 Status:** {site['status']}")
        
        # Export options
        st.subheader("📥 Export Real Results")
        
        # Create DataFrame for export
        df_data = []
        for site in results:
            df_data.append({
                'URL': site['url'],
                'Title': site['title'],
                'Quality_Score': site['quality_score'],
                'Emails': ', '.join(site['emails']) if site['emails'] else 'Not found',
                'Guest_Indicators': ', '.join(site['guest_indicators']),
                'Contact_Page': 'Yes' if site['contact_found'] else 'No',
                'Content_Length': site['content_length']
            })
        
        df = pd.DataFrame(df_data)
        
        col1, col2 = st.columns(2)
        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                label="💾 Download CSV",
                data=csv,
                file_name=f"real_guest_posts_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                type="primary"
            )
        
        with col2:
            json_data = df.to_json(orient='records', indent=2)
            st.download_button(
                label="📄 Download JSON",
                data=json_data,
                file_name=f"real_guest_posts_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )
    
    else:
        st.error(f"❌ No guest posting sites found for '{keyword}' in real search")
        st.info("""
        **🔧 Try these solutions:**
        1. **Use more specific keywords** - Instead of "game", try "game development", "gaming technology", "video game reviews"
        2. **Try different niches** - "digital marketing", "technology", "health", "business"
        3. **Check your internet connection**
        4. **Wait a few minutes and try again** - Search engines might be temporarily busy
        
        **💡 Example keywords that work well:**
        - "digital marketing"
        - "web development" 
        - "health technology"
        - "personal finance"
        - "business strategy"
        """)

if __name__ == "__main__":
    main()
