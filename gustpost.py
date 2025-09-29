import requests
from bs4 import BeautifulSoup
import re
import json
import time
import random
from urllib.parse import urljoin, urlparse
import pandas as pd
from dataclasses import dataclass, asdict
from typing import List, Dict
import warnings
warnings.filterwarnings('ignore')

@dataclass
class GuestPostPage:
    title: str
    url: str
    domain: str
    description: str
    emails: List[str]
    contact_forms: List[str]
    guidelines_url: str
    requirements: List[str]
    is_guest_page: bool
    confidence_score: int

class LiveGuestPostFinder:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Guest post indicators
        self.guest_post_indicators = [
            'write for us', 'guest post', 'submit article', 'contribute',
            'guest author', 'become a contributor', 'submission guidelines',
            'write for our blog', 'guest blogger', 'freelance writer',
            'submit content', 'author guidelines', 'contributor',
            'guest writing', 'blog submission', 'article submission'
        ]
        
        # URL patterns that indicate guest post pages
        self.url_patterns = [
            'write-for-us', 'guest-post', 'submit-article', 'contribute',
            'guest-author', 'write-for-our-blog', 'submission-guidelines',
            'author-guidelines', 'contributor', 'submissions', 'write'
        ]

    def search_google(self, query: str, num_results: int = 20) -> List[str]:
        """Search Google for guest post pages"""
        urls = []
        try:
            # Using Google Custom Search or DuckDuckGo as fallback
            search_url = f"https://html.duckduckgo.com/html/?q={query}"
            
            response = self.session.get(search_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract URLs from search results
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('/l/?uddg='):
                    # Extract real URL from DuckDuckGo redirect
                    try:
                        real_url = href.split('uddg=')[1].split('&')[0]
                        from urllib.parse import unquote
                        real_url = unquote(real_url)
                        if self.is_valid_url(real_url):
                            urls.append(real_url)
                    except:
                        continue
                        
            return list(set(urls))[:num_results]
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and not from excluded domains"""
        excluded_domains = ['google.com', 'facebook.com', 'twitter.com', 'linkedin.com', 'youtube.com']
        try:
            parsed = urlparse(url)
            return (parsed.netloc and 
                    not any(domain in parsed.netloc for domain in excluded_domains) and
                    url.startswith(('http://', 'https://')))
        except:
            return False

    def generate_search_queries(self, niche: str) -> List[str]:
        """Generate search queries for finding guest post pages"""
        queries = [
            f'"{niche}" "write for us"',
            f'"{niche}" "guest post"',
            f'"{niche}" "submit article"',
            f'"{niche}" "contribute"',
            f'"{niche}" "guest author"',
            f'"{niche}" inurl:write-for-us',
            f'"{niche}" inurl:guest-post',
            f'"{niche}" inurl:contribute',
            f'"{niche}" "submission guidelines"',
            f'"{niche}" "become a contributor"',
            f'"{niche}" "freelance writer"',
            f'"{niche}" "author guidelines"',
            f'intitle:"write for us" "{niche}"',
            f'intitle:"guest post" "{niche}"',
            f'"{niche}" site:wordpress.com "write for us"',
            f'"{niche}" site:medium.com "write"',
            f'"{niche}" "submit your post"',
            f'"{niche}" "guest blogger"',
            f'"{niche}" "write for our blog"',
            f'"{niche}" "blog submission"'
        ]
        return queries

    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        # Filter out common false positives
        valid_emails = []
        for email in emails:
            if not any(x in email.lower() for x in ['example.com', 'test.com', 'sample.com', 'yoursite.com']):
                valid_emails.append(email)
        return list(set(valid_emails))

    def find_contact_forms(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find contact form URLs"""
        forms = []
        for form in soup.find_all('form'):
            action = form.get('action')
            if action:
                full_url = urljoin(base_url, action)
                if any(word in action.lower() for word in ['contact', 'submit', 'form']):
                    forms.append(full_url)
        
        # Also look for contact page links
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if any(word in href for word in ['contact', 'submit', 'form']) and 'mailto:' not in href:
                full_url = urljoin(base_url, link['href'])
                forms.append(full_url)
                
        return list(set(forms))

    def extract_requirements(self, text: str) -> List[str]:
        """Extract submission requirements from text"""
        requirements = []
        text_lower = text.lower()
        
        # Common requirement patterns
        patterns = {
            'word count': r'(\d+[\+\-\s]*words?)',
            'original content': r'(original\s+content|unique\s+content|plagiarism)',
            'author bio': r'(author\s+bio|bio\s+required|about\s+author)',
            'links': r'(no\s+follow|do\s+follow|backlink)',
            'images': r'(images?\s+required|include\s+images?)',
            'format': r'(markdown|html|word\s+document|google\s+docs)',
        }
        
        for req_type, pattern in patterns.items():
            matches = re.findall(pattern, text_lower)
            if matches:
                requirements.extend(matches)
        
        # Look for bullet points or numbered lists
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if (line.startswith(('•', '-', '*', '1.', '2.', '3.')) and 
                len(line) > 10 and len(line) < 100):
                requirements.append(line)
        
        return requirements[:10]  # Limit to top 10

    def is_guest_post_page(self, soup: BeautifulSoup, url: str, text: str) -> tuple:
        """Determine if this is actually a guest post page"""
        score = 0
        reasons = []
        
        # Check URL patterns
        for pattern in self.url_patterns:
            if pattern in url.lower():
                score += 30
                reasons.append(f"URL contains '{pattern}'")
        
        # Check content for guest post indicators
        text_lower = text.lower()
        for indicator in self.guest_post_indicators:
            if indicator in text_lower:
                score += 10
                reasons.append(f"Content mentions '{indicator}'")
        
        # Check title
        title = soup.title.string if soup.title else ""
        title_lower = title.lower()
        for indicator in ['write for us', 'guest post', 'contribute', 'submission']:
            if indicator in title_lower:
                score += 25
                reasons.append(f"Title contains '{indicator}'")
        
        # Check for forms or email addresses
        forms = soup.find_all('form')
        if forms:
            score += 15
            reasons.append("Has contact forms")
        
        emails = self.extract_emails(text)
        if emails:
            score += 20
            reasons.append(f"Has {len(emails)} email addresses")
        
        # Check for submission guidelines
        if any(word in text_lower for word in ['guidelines', 'requirements', 'criteria']):
            score += 15
            reasons.append("Has submission guidelines")
        
        return score >= 40, score, reasons

    def analyze_page(self, url: str) -> GuestPostPage:
        """Analyze a single page for guest post opportunities"""
        try:
            response = self.session.get(url, timeout=15, allow_redirects=True)
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()
            
            # Extract basic info
            title = soup.title.string.strip() if soup.title and soup.title.string else "No title"
            domain = urlparse(url).netloc
            description = ""
            
            # Get meta description or first paragraph
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '')
            else:
                # Get first paragraph
                paragraphs = soup.find_all('p')
                for p in paragraphs:
                    if len(p.get_text().strip()) > 50:
                        description = p.get_text().strip()[:200]
                        break
            
            # Extract contact information
            emails = self.extract_emails(text)
            contact_forms = self.find_contact_forms(soup, url)
            requirements = self.extract_requirements(text)
            
            # Check if this is actually a guest post page
            is_guest, confidence, reasons = self.is_guest_post_page(soup, url, text)
            
            return GuestPostPage(
                title=title,
                url=url,
                domain=domain,
                description=description,
                emails=emails,
                contact_forms=contact_forms,
                guidelines_url=url if is_guest else "",
                requirements=requirements,
                is_guest_page=is_guest,
                confidence_score=confidence
            )
            
        except Exception as e:
            print(f"Error analyzing {url}: {e}")
            return None

    def find_guest_posts(self, niche: str, max_results: int = 50) -> List[GuestPostPage]:
        """Main function to find guest post opportunities"""
        print(f"🔍 Searching for guest post opportunities in '{niche}' niche...")
        
        all_urls = []
        queries = self.generate_search_queries(niche)
        
        # Search with different queries
        for i, query in enumerate(queries[:10]):  # Limit queries to avoid being blocked
            print(f"Searching with query {i+1}/10: {query}")
            urls = self.search_google(query, max_results // 5)
            all_urls.extend(urls)
            time.sleep(random.uniform(1, 3))  # Random delay
        
        # Remove duplicates
        unique_urls = list(set(all_urls))[:max_results * 2]
        print(f"Found {len(unique_urls)} unique URLs to analyze...")
        
        # Analyze each URL
        results = []
        for i, url in enumerate(unique_urls):
            print(f"Analyzing {i+1}/{len(unique_urls)}: {url}")
            page = self.analyze_page(url)
            if page and page.is_guest_page:
                results.append(page)
            time.sleep(random.uniform(0.5, 1.5))  # Delay between requests
        
        # Sort by confidence score
        results.sort(key=lambda x: x.confidence_score, reverse=True)
        return results[:max_results]

    def export_to_csv(self, results: List[GuestPostPage], filename: str):
        """Export results to CSV"""
        data = []
        for page in results:
            data.append({
                'Title': page.title,
                'URL': page.url,
                'Domain': page.domain,
                'Description': page.description,
                'Emails': ', '.join(page.emails),
                'Contact Forms': ', '.join(page.contact_forms),
                'Requirements': ', '.join(page.requirements),
                'Confidence Score': page.confidence_score,
                'Is Guest Page': page.is_guest_page
            })
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"✅ Results exported to {filename}")

    def export_to_json(self, results: List[GuestPostPage], filename: str):
        """Export results to JSON"""
        data = [asdict(page) for page in results]
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Results exported to {filename}")

def main():
    finder = LiveGuestPostFinder()
    
    # Get user input
    niche = input("Enter your niche (e.g., technology, business, health): ").strip()
    max_results = int(input("How many results do you want? (default: 20): ") or "20")
    
    if not niche:
        print("❌ Please enter a niche!")
        return
    
    # Find guest post opportunities
    results = finder.find_guest_posts(niche, max_results)
    
    if not results:
        print("❌ No guest post pages found. Try a different niche or search terms.")
        return
    
    print(f"\n🎉 Found {len(results)} guest post opportunities!")
    print("="*50)
    
    # Display results
    for i, page in enumerate(results, 1):
        print(f"\n{i}. {page.title}")
        print(f"   URL: {page.url}")
        print(f"   Domain: {page.domain}")
        print(f"   Emails: {', '.join(page.emails) if page.emails else 'None found'}")
        print(f"   Confidence: {page.confidence_score}/100")
        if page.requirements:
            print(f"   Requirements: {', '.join(page.requirements[:3])}...")
        print("-" * 50)
    
    # Export options
    export_choice = input("\nExport results? (csv/json/no): ").strip().lower()
    if export_choice == 'csv':
        filename = f"{niche}_guest_posts.csv"
        finder.export_to_csv(results, filename)
    elif export_choice == 'json':
        filename = f"{niche}_guest_posts.json"
        finder.export_to_json(results, filename)

if __name__ == "__main__":
    main()
