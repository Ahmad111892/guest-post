# gustpost_streamlit.py
# Streamlit web UI for the Ultra-Advanced Guest Post Finder
# Single-file Streamlit app suitable for GitHub + Streamlit Cloud deployment

import streamlit as st
import time
import random
import re
import csv
import json
import urllib.parse as up
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime

# Optional imports
try:
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
except Exception:
    requests = None
    BeautifulSoup = None
    pd = None

# -----------------------------
# Config / Patterns (same logic as CLI version)
# -----------------------------
ADVANCED_PATTERNS = [
    '"{}" "write for us"',
    '"{}" "guest post"',
    '"{}" "submit article"',
    '"{}" inurl:write-for-us',
    '"{}" intitle:"write for us"',
    '"{}" filetype:pdf "submission guidelines"',
    '"{}" "accepting guest posts"',
    '"{}" "sponsored post"',
    '"{}" "writers wanted"',
]

REGEX_ONPAGE = [
    re.compile(r'write\s+for\s+us', re.I),
    re.compile(r'(submit|send)\s+(your\s+)?(article|post|content)', re.I),
    re.compile(r'submission\s+guidelines', re.I),
    re.compile(r'guest\s+(post|posting|author|contributor)', re.I),
]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15',
]

WEIGHTS = {
    'title_exact': 3.0,
    'url_write_for_us': 2.5,
    'filetype_guideline': 2.0,
    'snippet_guidelines': 2.0,
    'onpage_hits': 0.8,
}

THRESHOLDS = {'platinum': 6.0, 'gold': 4.0, 'silver': 2.0, 'bronze': 0.5}

# -----------------------------
# Helpers & core functions
# -----------------------------

def extract_domain(url: str) -> str:
    try:
        netloc = up.urlparse(url).netloc.lower()
        if netloc.startswith('www.'):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return url


def normalize_url(url: str) -> str:
    try:
        parsed = up.urlparse(url)
        clean_query = up.parse_qsl(parsed.query)
        clean_query = [(k, v) for (k, v) in clean_query if not k.lower().startswith(('utm_', 'fbclid', 'gclid'))]
        new_q = up.urlencode(clean_query)
        return up.urlunparse((parsed.scheme or 'https', parsed.netloc, parsed.path.rstrip('/'), '', new_q, ''))
    except Exception:
        return url


def safe_get(url: str, timeout: int = 12) -> Optional[str]:
    if requests is None:
        return None
    try:
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return r.text
    except Exception:
        return None
    return None


def generate_queries(keywords: List[str], patterns: List[str]) -> List[str]:
    queries = []
    for kw in keywords:
        for p in patterns:
            queries.append(p.format(kw))
    # dedupe
    seen = set(); out = []
    for q in queries:
        if q not in seen:
            seen.add(q); out.append(q)
    return out

@dataclass
class SerpResult:
    query: str
    title: str
    url: str
    snippet: str

@dataclass
class Candidate:
    query: str
    url: str
    title: str
    snippet: str
    domain: str
    base_score: float
    onpage_hits: int
    onpage_boost: float
    total_score: float
    label: str

# Lightweight SERP via DuckDuckGo HTML

def search_duckduckgo_html(query: str, tld: str = 'com', kl: str = 'us-en', limit: int = 10) -> List[SerpResult]:
    out = []
    if requests is None or BeautifulSoup is None:
        return out
    try:
        params = {'q': query, 'kl': kl}
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        r = requests.get(f'https://duckduckgo.{tld}/html/', params=params, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for res in soup.select('.result')[:limit]:
            a = res.select_one('.result__a')
            if not a: continue
            url = a.get('href', '')
            title = a.get_text(' ', strip=True)
            snippet_el = res.select_one('.result__snippet')
            snippet = snippet_el.get_text(' ', strip=True) if snippet_el else ''
            out.append(SerpResult(query=query, title=title, url=url, snippet=snippet))
    except Exception:
        pass
    return out


def quick_score(title: str, url: str, snippet: str) -> float:
    t = (title or '').lower(); u = (url or '').lower(); s = (snippet or '').lower()
    score = 0.0
    if 'write for us' in t: score += WEIGHTS['title_exact']
    if any(k in u for k in ['write-for-us','guest-post','submission-guidelines']): score += WEIGHTS['url_write_for_us']
    if any(ft in s for ft in ['submission guideline','editorial guideline']): score += WEIGHTS['snippet_guidelines']
    if any(url.lower().endswith(ext) for ext in ['.pdf','.doc','.docx']): score += WEIGHTS['filetype_guideline']
    return score


def onpage_verify(url: str) -> Tuple[int, float]:
    html_text = safe_get(url) or ''
    if not html_text:
        return 0, 0.0
    hits = 0
    for rx in REGEX_ONPAGE:
        if rx.search(html_text): hits += 1
    return hits, hits * WEIGHTS['onpage_hits']


def label_from_score(score: float) -> str:
    if score >= THRESHOLDS['platinum']: return 'platinum'
    if score >= THRESHOLDS['gold']: return 'gold'
    if score >= THRESHOLDS['silver']: return 'silver'
    if score >= THRESHOLDS['bronze']: return 'bronze'
    return 'low'

# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(page_title='GuestPost Finder', layout='wide')
st.title('GuestPost Finder — Streamlit Web UI')

with st.sidebar:
    st.header('Settings')
    keywords_input = st.text_area('Keywords (comma separated)', value='health,fitness')
    use_duck = st.checkbox('Use DuckDuckGo fallback', value=True)
    limit = st.slider('Results per query', min_value=5, max_value=50, value=10)
    tld = st.text_input('Search TLD', value='com')
    polite_delay = st.number_input('Delay between queries (s)', min_value=0.1, max_value=10.0, value=1.0)
    no_onpage = st.checkbox('Skip on-page verification', value=False)
    serpapi_key = st.text_input('SerpApi Key (optional)', type='password')
    run_button = st.button('Run Search')

col1, col2 = st.columns([2,1])

with col1:
    st.subheader('Generated Queries (preview)')
    if keywords_input.strip():
        keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
        queries = generate_queries(keywords, ADVANCED_PATTERNS)
        st.write(f'Generated {len(queries)} queries')
        st.code('\n'.join(queries[:200]))
    else:
        st.info('Enter keywords at left to preview queries')

with col2:
    st.subheader('Quick tips')
    st.markdown('- Use 1-5 keywords to start.\n- Toggle Skip on-page if it is too slow.\n- Provide SerpApi key for Google results (faster & more reliable).')

# Results area
placeholder = st.empty()

if run_button:
    if not keywords_input.strip():
        st.warning('Enter at least one keyword in the sidebar')
    else:
        keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
        queries = generate_queries(keywords, ADVANCED_PATTERNS)
        total_queries = len(queries)
        st.info(f'Starting search for {len(keywords)} keywords => {total_queries} queries')

        # Iterate queries and collect candidates
        candidates = []
        progress = st.progress(0)
        p = 0
        for i, q in enumerate(queries):
            serp_results = []
            if serpapi_key:
                # lightweight: call SerpApi if key provided
                try:
                    params = {
                        'engine': 'google', 'q': q, 'api_key': serpapi_key, 'num': limit,
                    }
                    r = requests.get('https://serpapi.com/search.json', params=params, timeout=18)
                    data = r.json()
                    for item in data.get('organic_results', [])[:limit]:
                        serp_results.append(SerpResult(query=q, title=item.get('title',''), url=item.get('link',''), snippet=item.get('snippet','')))
                except Exception:
                    serp_results = []
            if (not serp_results) and use_duck:
                serp_results = search_duckduckgo_html(q, tld=tld, kl='us-en', limit=limit)

            for r in serp_results[:limit]:
                u_norm = normalize_url(r.url)
                base = quick_score(r.title, u_norm, r.snippet)
                hits, boost = (0, 0.0) if no_onpage else onpage_verify(u_norm)
                total = base + boost
                cand = Candidate(query=q, url=u_norm, title=r.title[:200], snippet=r.snippet[:300], domain=extract_domain(u_norm), base_score=base, onpage_hits=hits, onpage_boost=boost, total_score=total, label=label_from_score(total))
                candidates.append(cand)

            # polite delay
            time.sleep(polite_delay + random.random()*0.6)
            p = int(((i+1)/total_queries)*100)
            progress.progress(min(p, 100))

        # Deduplicate and sort
        seen: Set[str] = set(); final = []
        for c in candidates:
            if c.url in seen: continue
            seen.add(c.url); final.append(c)
        final.sort(key=lambda x: x.total_score, reverse=True)

        st.success(f'Collected {len(final)} candidates')

        # Show dataframe if pandas available
        if pd is not None:
            df = pd.DataFrame([{
                'label': c.label, 'score': round(c.total_score,2), 'domain': c.domain, 'url': c.url,
                'title': c.title, 'snippet': c.snippet, 'onpage_hits': c.onpage_hits, 'query': c.query
            } for c in final])
            st.dataframe(df.head(200))

            csv_bytes = df.to_csv(index=False).encode('utf-8')
            st.download_button('Download CSV', data=csv_bytes, file_name='guestpost_results.csv', mime='text/csv')
            st.download_button('Download JSON', data=df.to_json(orient='records', force_ascii=False).encode('utf-8'), file_name='guestpost_results.json', mime='application/json')
        else:
            # simple print
            for c in final[:200]:
                st.write(f"[{c.label}] {c.total_score:.2f} — {c.domain}")
                st.write(c.title)
                st.write(c.url)
                st.write(c.snippet)
                st.write('---')

        st.balloons()

# Footer
st.markdown('---')
st.caption('GuestPost Finder — Streamlit single-file app. Save to GitHub and deploy to Streamlit Cloud.')
