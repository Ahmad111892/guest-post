# gustpost_streamlit.py
# Streamlit web UI — Bing HTML Scraper (100 results per query) — Skip Ads — Table view
#
# Usage:
#   streamlit run gustpost_streamlit.py
#
# Requirements:
#   pip install streamlit requests beautifulsoup4 lxml pandas
#
# Notes:
# - This app uses Bing HTML scraping (no API key). It requests two pages of 50 results
#   each (count=50, first=0 and first=50) to reach ~100 results per query.
# - Ads / sponsored blocks are skipped (selectors: .b_ad, .b_algoSponsored, .b_ans).
# - Results are shown in a pandas DataFrame with download buttons for CSV/JSON.
# - Keep polite delays and avoid aggressive scraping on many queries at once.
# - This file is intended to be saved to GitHub and deployed to Streamlit Cloud.

import streamlit as st
import time
import random
import re
import urllib.parse as up
from dataclasses import dataclass
from typing import List, Optional, Tuple, Set
from datetime import datetime

# optional imports
try:
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
except Exception:
    requests = None
    BeautifulSoup = None
    pd = None

# -----------------------------
# Config / Patterns
# -----------------------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
]

ADVANCED_PATTERNS = [
    # kept compact for UI preview; generator still useful
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

WEIGHTS = {
    'title_exact': 3.0,
    'url_write_for_us': 2.5,
    'filetype_guideline': 2.0,
    'snippet_guidelines': 2.0,
    'onpage_hits': 0.8,
    'recency_boost': 0.5,
}

THRESHOLDS = {'platinum': 6.0, 'gold': 4.0, 'silver': 2.0, 'bronze': 0.5}

# -----------------------------
# Helpers
# -----------------------------
def extract_domain(url: str) -> str:
    try:
        netloc = up.urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return url

def normalize_url(url: str) -> str:
    try:
        parsed = up.urlparse(url)
        clean_query = up.parse_qsl(parsed.query)
        clean_query = [(k, v) for (k, v) in clean_query if not k.lower().startswith(("utm_", "fbclid", "gclid", "mc_", "mkt_"))]
        new_q = up.urlencode(clean_query)
        scheme = parsed.scheme if parsed.scheme else "https"
        return up.urlunparse((scheme, parsed.netloc, parsed.path.rstrip('/'), '', new_q, ''))
    except Exception:
        return url

def safe_get(url: str, timeout: int = 12) -> Optional[str]:
    if requests is None:
        return None
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        if r.status_code == 200 and r.text:
            return r.text
    except Exception:
        return None
    return None

def year_in_text(text: str) -> bool:
    years = re.findall(r'(20[1-3]\d)', text)
    return bool(years)

# -----------------------------
# Query generation
# -----------------------------
def generate_queries(keywords: List[str], patterns: List[str]) -> List[str]:
    queries = []
    for kw in keywords:
        for p in patterns:
            try:
                queries.append(p.format(kw))
            except Exception:
                continue
    # dedupe preserve order
    seen = set()
    deduped = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            deduped.append(q)
    return deduped

# -----------------------------
# Bing scraper (HTML)
# -----------------------------
@dataclass
class SerpResult:
    query: str
    title: str
    url: str
    snippet: str

def parse_bing_html(html_text: str, skip_ads: bool = True) -> List[SerpResult]:
    """
    Parse Bing search HTML and extract organic results.
    We target list items with class 'b_algo'. Skip known ad/sponsored blocks.
    """
    out: List[SerpResult] = []
    if not html_text or BeautifulSoup is None:
        return out

    soup = BeautifulSoup(html_text, "lxml")

    # remove known ad/sponsored nodes early if skip_ads True
    if skip_ads:
        for sel in [".b_ad", ".b_algoSponsored", ".b_ans", ".b_supplemental"]:
            for node in soup.select(sel):
                node.decompose()

    # Organic results are usually in <li class="b_algo"> nodes
    items = soup.select("li.b_algo")
    for item in items:
        # Skip if it contains an ad badge or sponsored marker (defensive)
        if item.select_one(".b_ad"):
            continue
        # Title/link
        h2 = item.find("h2")
        if not h2:
            continue
        a = h2.find("a", href=True)
        if not a:
            continue
        url = a["href"].strip()
        title = a.get_text(" ", strip=True)
        # Snippet: b_caption p or .b_snippet
        snippet = ""
        cap = item.select_one(".b_caption p")
        if cap:
            snippet = cap.get_text(" ", strip=True)
        else:
            sn = item.select_one(".b_snippet")
            if sn:
                snippet = sn.get_text(" ", strip=True)
        out.append(SerpResult(query="", title=title, url=url, snippet=snippet))
    return out

def search_bing(query: str, tld: str = "com", results_per_query: int = 100, skip_ads: bool = True, polite_delay: float = 1.0) -> List[SerpResult]:
    """
    Fetch up to results_per_query results from Bing by paginating count=50 pages.
    Bing supports &count=50 and &first=N (0-indexed).
    We'll request pages: first=0 (count=50) and first=50 (count=50) if results_per_query > 50.
    """
    out: List[SerpResult] = []
    if requests is None:
        return out

    # prepare pages: each page up to 50
    page_size = 50
    pages = (results_per_query + page_size - 1) // page_size
    pages = max(1, min(pages, 4))  # limit pages to avoid insane scraping (max 200)
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    encoded_q = query

    for p in range(pages):
        first = p * page_size
        params = {
            "q": encoded_q,
            "count": page_size,
            "first": first
        }
        url = f"https://www.bing.{tld}/search"
        try:
            r = requests.get(url, params=params, headers=headers, timeout=18)
            if r.status_code != 200:
                # small backoff and continue
                time.sleep(1.0 + random.random()*0.7)
                continue
            page_results = parse_bing_html(r.text, skip_ads=skip_ads)
            # set query field
            for pr in page_results:
                pr.query = query
            out.extend(page_results)
        except Exception:
            # ignore page errors, continue to next
            pass
        # polite delay between pages
        time.sleep(polite_delay + random.random()*0.4)
    # dedupe by normalized url preserving order
    seen: Set[str] = set()
    deduped: List[SerpResult] = []
    for r in out:
        norm = normalize_url(r.url)
        if norm in seen:
            continue
        seen.add(norm)
        # attach normalized url
        r.url = norm
        deduped.append(r)
    return deduped[:results_per_query]

# -----------------------------
# Scoring & verification
# -----------------------------
def quick_score(title: str, url: str, snippet: str) -> float:
    t = (title or "").lower()
    u = (url or "").lower()
    s = (snippet or "").lower()
    score = 0.0
    if 'write for us' in t:
        score += WEIGHTS['title_exact']
    if any(k in u for k in ['write-for-us', 'guest-post', 'submission-guidelines', 'submit-guest-post']):
        score += WEIGHTS['url_write_for_us']
    if any(ft in s for ft in ['submission guideline', 'editorial guideline', 'submission guidelines']):
        score += WEIGHTS['snippet_guidelines']
    if any(u.endswith(ext) for ext in ['.pdf', '.doc', '.docx']):
        score += WEIGHTS['filetype_guideline']
    if year_in_text(t) or year_in_text(s):
        score += WEIGHTS['recency_boost']
    return score

def onpage_verify(url: str) -> Tuple[int, float]:
    html_text = safe_get(url) or ""
    if not html_text:
        return 0, 0.0
    hits = 0
    for rx in REGEX_ONPAGE:
        if rx.search(html_text):
            hits += 1
    return hits, hits * WEIGHTS['onpage_hits']

def label_from_score(score: float) -> str:
    if score >= THRESHOLDS['platinum']:
        return 'platinum'
    if score >= THRESHOLDS['gold']:
        return 'gold'
    if score >= THRESHOLDS['silver']:
        return 'silver'
    if score >= THRESHOLDS['bronze']:
        return 'bronze'
    return 'low'

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="GuestPost Finder (Bing)", layout="wide")
st.title("GuestPost Finder — Bing Scraper (100 results)")

with st.sidebar:
    st.header("Settings")
    keywords_input = st.text_area("Keywords (comma separated)", value="health,fitness")
    results_per_query = st.selectbox("Results per query (target)", options=[10, 20, 50, 100], index=3)
    tld = st.text_input("Bing TLD", value="com")
    polite_delay = st.number_input("Delay between requests (s)", min_value=0.1, max_value=5.0, value=1.0)
    run_button = st.button("Run Search")
    skip_onpage = st.checkbox("Skip on-page verification (faster)", value=False)

col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Generated Queries (preview)")
    if keywords_input.strip():
        keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
        queries = generate_queries(keywords, ADVANCED_PATTERNS)
        st.write(f"Generated {len(queries)} queries for {len(keywords)} keywords")
        # show only first 200 queries
        preview_join = "\n".join(queries[:200])
        st.code(preview_join)
    else:
        st.info("Enter keywords in the sidebar to preview queries.")

with col2:
    st.subheader("Quick tips")
    st.markdown(
        """
- Use a few focused keywords (1–5) to start.
- `Skip on-page` to drastically speed up runs.
- Avoid running too many queries in parallel — be polite to Bing.
"""
    )

placeholder = st.empty()

if run_button:
    if not keywords_input.strip():
        st.warning("Enter at least one keyword in the sidebar")
    else:
        keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
        queries = generate_queries(keywords, ADVANCED_PATTERNS)
        total_queries = len(queries)
        st.info(f"Starting search for {len(keywords)} keywords → {total_queries} queries (target {results_per_query} results each)")
        all_candidates = []
        prog = st.progress(0)
        for i, q in enumerate(queries):
            # Bing expects q as a normal query string. We use the pattern directly (it contains quotes).
            # urlencode is handled by requests.
            serp = []
            try:
                serp = search_bing(q, tld=tld, results_per_query=results_per_query, skip_ads=True, polite_delay=polite_delay)
            except Exception:
                serp = []
            # process results
            for r in serp:
                base = quick_score(r.title, r.url, r.snippet)
                hits = 0
                boost = 0.0
                if not skip_onpage:
                    try:
                        hits, boost = onpage_verify(r.url)
                    except Exception:
                        hits, boost = 0, 0.0
                total = base + boost
                cand = {
                    "label": label_from_score(total),
                    "score": round(total, 2),
                    "domain": extract_domain(r.url),
                    "url": r.url,
                    "title": r.title,
                    "snippet": r.snippet,
                    "onpage_hits": hits,
                    "query": q
                }
                all_candidates.append(cand)

            # polite short pause between queries
            time.sleep(max(0.2, polite_delay * 0.3))
            prog.progress(int(((i + 1) / total_queries) * 100))

        # dedupe by url, preserve best score (first highest wins due to ordering)
        seen: Set[str] = set()
        deduped = []
        for c in sorted(all_candidates, key=lambda x: x["score"], reverse=True):
            if c["url"] in seen:
                continue
            seen.add(c["url"])
            deduped.append(c)

        st.success(f"Collected {len(deduped)} candidates")

        if pd is not None:
            df = pd.DataFrame(deduped)
            # show top 200 rows
            st.dataframe(df.head(200))

            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", data=csv_bytes, file_name="guestpost_results.csv", mime="text/csv")
            json_bytes = df.to_json(orient="records", force_ascii=False).encode("utf-8")
            st.download_button("Download JSON", data=json_bytes, file_name="guestpost_results.json", mime="application/json")
        else:
            # fallback: simple listing
            for c in deduped[:200]:
                st.write(f"[{c['label']}] {c['score']} — {c['domain']}")
                st.write(c['title'])
                st.write(c['url'])
                if c['snippet']:
                    st.write(c['snippet'])
                st.write("---")

        st.balloons()

st.markdown("---")
st.caption("Built for GitHub → Streamlit Cloud. Use responsibly and respect search engine usage policies.")
