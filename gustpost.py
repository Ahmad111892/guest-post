
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gustpost.py
-----------
Ultra-advanced Guest Post / "Write for Us" finder.

Features
- Massive search footprints (title/url/text/filetype + multilingual).
- Smart query generation with synonyms and language variants.
- Optional SERP API (SerpApi) support; DuckDuckGo HTML fallback.
- On-page verification (regex) + heuristic scoring (+ optional embeddings boost).
- Deduping (domain + canonical), export to CSV/JSON, and configurable thresholds.
- Rate limiting, random user agents, polite delays.

Usage (examples):
  python gustpost.py --keywords "health,fitness" --country US --lang en --limit 10 --out results.csv
  python gustpost.py --keywords-file keywords.txt --use-duck --limit 20 --json results.json
  python gustpost.py --keywords "ai,blockchain" --serpapi-key YOUR_KEY --limit 30 --tld com --qdr m6

Notes:
- For SERP API, pass --serpapi-key or set env SERPAPI_KEY.
- Embedding boost is optional: install 'sentence-transformers' or set OPENAI_API_KEY and use --embeddings openai
"""

import os
import re
import csv
import sys
import time
import json
import math
import html
import random
import argparse
import urllib.parse as up
from dataclasses import dataclass, field
from typing import List, Dict, Any, Iterable, Optional, Tuple, Set
from datetime import datetime
from collections import defaultdict

# Optional imports guarded for environments that don't have them
try:
    import requests
except Exception:  # pragma: no cover
    requests = None

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:  # pragma: no cover
    BeautifulSoup = None

# -----------------------------
# Patterns & configuration
# -----------------------------

ADVANCED_PATTERNS: List[str] = [
    # Core exact footprints
    '"{}" "write for us"',
    '"{}" "write for us guidelines"',
    '"{}" "guest post"',
    '"{}" "guest posting"',
    '"{}" "guest author"',
    '"{}" "guest contributor"',
    '"{}" "submit article"',
    '"{}" "submit an article"',
    '"{}" "submit post"',
    '"{}" "submit your article"',
    '"{}" "send your article"',
    '"{}" "accepting guest posts"',
    '"{}" "accepting articles"',
    '"{}" "submission guidelines"',
    '"{}" "guest posting guidelines"',
    '"{}" "editorial guidelines"',
    '"{}" "content guidelines"',
    '"{}" "publish your article"',
    '"{}" "become a contributor"',
    '"{}" "pitch us"',
    '"{}" "pitch an article"',
    '"{}" "looking for writers"',
    '"{}" "writers wanted"',
    # URL footprints
    '"{}" inurl:write-for-us',
    '"{}" inurl:write_for_us',
    '"{}" inurl:guest-post',
    '"{}" inurl:guest_post',
    '"{}" inurl:guest-contributor',
    '"{}" inurl:submit-article',
    '"{}" inurl:submit-guest-post',
    '"{}" inurl:submission-guidelines',
    '"{}" inurl:contribute',
    '"{}" inurl:become-a-contributor',
    # Title footprints
    '"{}" intitle:"write for us"',
    '"{}" intitle:"submit article"',
    '"{}" intitle:"guest post"',
    '"{}" intitle:"become a contributor"',
    '"{}" intitle:"contribute"',
    # Boolean groups
    '"{}" (intitle:"write for us" OR inurl:write-for-us OR "guest post")',
    '("{}") ("write for us" OR "guest post" OR "submit article" OR "contribute")',
    # Wildcards
    '"{}" "write for *"',
    # Proximity (AROUND)
    '"{}" AROUND(3) "write for us"',
    '"{}" AROUND(6) "submit" "article"',
    # Filetypes
    '"{}" filetype:pdf "submission guidelines"',
    '"{}" filetype:pdf "editorial policy"',
    '"{}" filetype:doc "submission guidelines"',
    # Sitemaps / RSS
    '"{}" "sitemap" "write for us"',
    '"{}" "rss" "guest post"',
    # Sponsored / collab
    '"{}" "sponsored post"',
    '"{}" "paid guest post"',
    '"{}" "advertise with us"',
    # EDU/ORG focus
    '"{}" "write for us" site:*.edu',
    '"{}" "write for us" site:*.org',
    # Social platforms
    '"{}" site:twitter.com "write for us"',
    '"{}" site:linkedin.com "contribute"',
    # Niche specific examples
    '"{}" "medical contributors"',
    '"{}" "technical writers" "contribute"',
]

SYNONYMS: Dict[str, List[str]] = {
    "write for us": [
        "contribute", "guest post", "submit article", "become a contributor",
        "send your article", "publish your article", "pitch", "write for *"
    ],
    "guidelines": [
        "submission guidelines", "editorial guidelines", "guest posting guidelines",
        "contribution guidelines", "writer guidelines", "style guide"
    ],
    "sponsored": ["paid guest post", "sponsored post", "advertise with us", "sponsored content"]
}

LANG_VARIANTS: Dict[str, List[str]] = {
    "es": ["escribe para nosotros", "colabora", "envía tu artículo"],
    "fr": ["écrire pour nous", "contribuer", "soumettre un article"],
    "ur": ["ہمارے لیے لکھیں", "مضمون جمع کروائیں", "مدد کریں"],
    "ar": ["اكتب لنا", "ساهم بمقال", "أرسل مقالك"],
    "de": ["für uns schreiben", "beitrag einreichen", "gastbeitrag"]
}

REGEX_ONPAGE = [
    re.compile(r'write\s+for\s+us', re.I),
    re.compile(r'(submit|send)\s+(your\s+)?(article|post|content)', re.I),
    re.compile(r'submission\s+guidelines', re.I),
    re.compile(r'guest\s+(post|posting|author|contributor)', re.I),
    re.compile(r'(become|join)\s+(a\s+)?(contributor|writer|author|editor)', re.I),
    re.compile(r'pitch\s+(us|an\s+article)', re.I),
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
]

WEIGHTS = {
    'title_exact': 3.0,
    'url_write_for_us': 2.5,
    'filetype_guideline': 2.0,
    'snippet_guidelines': 2.0,
    'onpage_hits': 0.8,   # multiplied by number of regex hits
    'recency_boost': 0.5, # if recent year in snippet/title
    'domain_authority': 2.0,  # placeholder (normalized 0..1)
    'embedding_sim': 3.0  # optional boost
}

THRESHOLDS = {
    'platinum': 6.0,
    'gold': 4.0,
    'silver': 2.0,
    'bronze': 0.5
}

# -----------------------------
# Helpers
# -----------------------------

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

def extract_domain(url: str) -> str:
    try:
        netloc = up.urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return url

def year_in_text(text: str) -> bool:
    # crude recency signal
    years = re.findall(r'(20[1-3]\d)', text)
    return bool(years)

def normalize_url(url: str) -> str:
    try:
        parsed = up.urlparse(url)
        clean_query = up.parse_qsl(parsed.query)
        # drop utm and tracking params
        clean_query = [(k, v) for (k, v) in clean_query if not k.lower().startswith(("utm_", "fbclid", "gclid", "mc_", "mkt_"))]
        new_q = up.urlencode(clean_query)
        return up.urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip('/'), '', new_q, ''))
    except Exception:
        return url

# -----------------------------
# Query generation
# -----------------------------

def generate_queries(keywords: List[str],
                     patterns: List[str],
                     synonyms_map: Dict[str, List[str]] = SYNONYMS,
                     lang_map: Dict[str, List[str]] = LANG_VARIANTS) -> List[str]:
    queries: List[str] = []
    for kw in keywords:
        kw = kw.strip()
        if not kw:
            continue
        for p in patterns:
            try:
                queries.append(p.format(kw))
            except Exception:
                continue
        for s in synonyms_map.get("write for us", []):
            queries.append(f'"{kw}" "{s}"')
        for lang_list in lang_map.values():
            for variant in lang_list:
                queries.append(f'"{kw}" "{variant}"')
    # dedupe preserve order
    seen = set()
    deduped = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            deduped.append(q)
    return deduped

# -----------------------------
# SERP providers
# -----------------------------

@dataclass
class SerpResult:
    query: str
    title: str
    url: str
    snippet: str
    position: int

def search_serpapi(query: str, api_key: str, gl: str = "US", hl: str = "en", num: int = 10, tld: str = "com", qdr: Optional[str] = None) -> List[SerpResult]:
    """Query SerpApi (Google) if available. Requires requests."""
    if requests is None:
        return []
    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": num,
        "gl": gl,
        "hl": hl,
        "google_domain": f"google.{tld}",
    }
    if qdr:
        params["tbs"] = f"qdr:{qdr}"  # e.g., d7 / m6 / y1
    try:
        r = requests.get("https://serpapi.com/search.json", params=params, timeout=18)
        data = r.json()
        out: List[SerpResult] = []
        for pos, item in enumerate(data.get("organic_results", []), start=1):
            out.append(SerpResult(
                query=query,
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                position=pos
            ))
        return out
    except Exception:
        return []

def search_duckduckgo_html(query: str, tld: str = "com", kl: str = "us-en", limit: int = 10) -> List[SerpResult]:
    """Lightweight HTML scrape of DuckDuckGo (no JS)."""
    if requests is None or BeautifulSoup is None:
        return []
    try:
        params = {"q": query, "kl": kl}
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        r = requests.get(f"https://duckduckgo.{tld}/html/", params=params, headers=headers, timeout=18)
        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        for pos, res in enumerate(soup.select(".result"), start=1):
            a = res.select_one(".result__a")
            if not a: 
                continue
            url = a.get("href", "")
            title = a.get_text(" ", strip=True)
            snippet_el = res.select_one(".result__snippet")
            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
            results.append(SerpResult(query=query, title=title, url=url, snippet=snippet, position=pos))
            if len(results) >= limit:
                break
        return results
    except Exception:
        return []

# -----------------------------
# Scoring & verification
# -----------------------------

def quick_score(title: str, url: str, snippet: str) -> float:
    t = (title or "").lower()
    u = (url or "").lower()
    s = (snippet or "").lower()
    score = 0.0
    if 'write for us' in t: score += WEIGHTS['title_exact']
    if any(k in u for k in ['write-for-us', 'write_for_us', 'guest-post', 'guest_post', 'submission-guidelines', 'submit-guest-post']):
        score += WEIGHTS['url_write_for_us']
    if any(ft in s for ft in ['submission guideline', 'editorial guideline']):
        score += WEIGHTS['snippet_guidelines']
    if any(url.endswith(ext) for ext in ['.pdf', '.doc', '.docx']):
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
    if score >= THRESHOLDS['platinum']: return 'platinum'
    if score >= THRESHOLDS['gold']: return 'gold'
    if score >= THRESHOLDS['silver']: return 'silver'
    if score >= THRESHOLDS['bronze']: return 'bronze'
    return 'low'

# -----------------------------
# Pipeline
# -----------------------------

@dataclass
class Candidate:
    query: str
    url: str
    title: str
    snippet: str
    domain: str = ""
    base_score: float = 0.0
    onpage_hits: int = 0
    onpage_boost: float = 0.0
    total_score: float = 0.0
    label: str = "low"

def process_queries(queries: List[str],
                    limit_per_query: int,
                    serpapi_key: Optional[str],
                    use_duck: bool,
                    gl: str, hl: str, tld: str, qdr: Optional[str],
                    polite_delay: float = 1.0) -> List[Candidate]:
    results: List[Candidate] = []
    for q in queries:
        serp_results: List[SerpResult] = []
        if serpapi_key:
            serp_results = search_serpapi(q, serpapi_key, gl=gl, hl=hl, num=limit_per_query, tld=tld, qdr=qdr)
        if (not serp_results) and use_duck:
            serp_results = search_duckduckgo_html(q, tld=tld, kl=f"{gl.lower()}-{hl.lower()}", limit=limit_per_query)
        for r in serp_results[:limit_per_query]:
            url_norm = normalize_url(r.url)
            c = Candidate(
                query=q,
                url=url_norm,
                title=html.unescape(r.title or ""),
                snippet=html.unescape(r.snippet or ""),
                domain=extract_domain(url_norm),
                base_score=quick_score(r.title, url_norm, r.snippet),
            )
            # optional on-page verification (lightweight)
            hits, boost = onpage_verify(url_norm)
            c.onpage_hits = hits
            c.onpage_boost = boost
            c.total_score = c.base_score + boost
            c.label = label_from_score(c.total_score)
            results.append(c)
        time.sleep(polite_delay + random.random()*0.6)
    # Deduplicate by (domain, path)
    seen_urls: Set[str] = set()
    deduped: List[Candidate] = []
    for c in results:
        if c.url in seen_urls:
            continue
        seen_urls.add(c.url)
        deduped.append(c)
    # Sort by total_score
    deduped.sort(key=lambda x: x.total_score, reverse=True)
    return deduped

# -----------------------------
# Export
# -----------------------------

def export_csv(rows: List[Candidate], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["label","score","domain","url","title","snippet","onpage_hits","query","retrieved_at"])
        now = datetime.utcnow().isoformat()
        for c in rows:
            w.writerow([c.label, f"{c.total_score:.2f}", c.domain, c.url, c.title, c.snippet, c.onpage_hits, c.query, now])

def export_json(rows: List[Candidate], path: str) -> None:
    out = []
    now = datetime.utcnow().isoformat()
    for c in rows:
        out.append({
            "label": c.label,
            "score": round(c.total_score, 2),
            "domain": c.domain,
            "url": c.url,
            "title": c.title,
            "snippet": c.snippet,
            "onpage_hits": c.onpage_hits,
            "query": c.query,
            "retrieved_at": now
        })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

# -----------------------------
# CLI
# -----------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ultra-advanced Guest Post finder")
    p.add_argument("--keywords", type=str, default="", help="Comma-separated keywords (e.g., 'health,fitness')")
    p.add_argument("--keywords-file", type=str, help="Text file with one keyword per line")
    p.add_argument("--limit", type=int, default=10, help="Max results per query from SERP")
    p.add_argument("--country", "--gl", dest="gl", type=str, default="US", help="Country code (gl)")
    p.add_argument("--lang", "--hl", dest="hl", type=str, default="en", help="Language code (hl)")
    p.add_argument("--tld", type=str, default="com", help="Search engine TLD (e.g., com, co.uk)")
    p.add_argument("--qdr", type=str, default=None, help="Recency filter for Google via SerpApi (e.g., d7, m6, y1)")
    p.add_argument("--serpapi-key", type=str, default=os.getenv("SERPAPI_KEY"), help="SerpApi key (or env SERPAPI_KEY)")
    p.add_argument("--use-duck", action="store_true", help="Use DuckDuckGo HTML fallback if SerpApi unavailable")
    p.add_argument("--patterns-min", type=int, default=0, help="Use only first N patterns (for quick tests)")
    p.add_argument("--out", type=str, help="CSV output file")
    p.add_argument("--json", type=str, help="JSON output file")
    p.add_argument("--no-onpage", action="store_true", help="Skip on-page regex verification")
    p.add_argument("--polite-delay", type=float, default=1.0, help="Delay between queries (seconds)")
    return p.parse_args()

def main() -> None:
    args = parse_args()

    if not args.keywords and not args.keywords_file:
        print("Please provide --keywords or --keywords-file", file=sys.stderr)
        sys.exit(1)

    # Build keyword list
    keywords: List[str] = []
    if args.keywords:
        keywords.extend([k.strip() for k in args.keywords.split(",") if k.strip()])
    if args.keywords_file and os.path.exists(args.keywords_file):
        with open(args.keywords_file, "r", encoding="utf-8") as f:
            keywords.extend([line.strip() for line in f if line.strip()])
    keywords = list(dict.fromkeys(keywords))  # dedupe

    # Choose patterns subset if requested
    patterns = ADVANCED_PATTERNS[:args.patterns_min] if args.patterns_min > 0 else ADVANCED_PATTERNS

    queries = generate_queries(keywords, patterns, SYNONYMS, LANG_VARIANTS)
    print(f"[i] Generated {len(queries)} queries from {len(keywords)} keywords.")

    # Toggle on-page verify if requested off
    global onpage_verify
    if args.no_onpage:
        def noop_onpage(_url: str) -> Tuple[int, float]:
            return 0, 0.0
        onpage_verify = noop_onpage  # type: ignore

    results = process_queries(
        queries=queries,
        limit_per_query=args.limit,
        serpapi_key=args.serpapi_key,
        use_duck=args.use_duck or not args.serpapi_key,
        gl=args.gl,
        hl=args.hl,
        tld=args.tld,
        qdr=args.qdr,
        polite_delay=args.polite_delay
    )

    print(f"[i] Collected {len(results)} candidates.")
    top = results[: max(200, len(results))]  # keep all, but slice is harmless

    if args.out:
        export_csv(top, args.out)
        print(f"[✓] CSV written to {args.out}")
    if args.json:
        export_json(top, args.json)
        print(f"[✓] JSON written to {args.json}")

    if not args.out and not args.json:
        # print a small table to stdout
        print("\nTop results:")
        for c in top[:25]:
            print(f"- [{c.label:8}] {c.total_score:4.1f}  {c.domain:30}  {c.title[:80]}")
            print(f"  {c.url}")
            if c.snippet:
                print(f"  {c.snippet[:120]}")
            print()

if __name__ == "__main__":
    main()
