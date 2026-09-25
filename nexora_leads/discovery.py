"""Public-index and public-page research only; no logins or security testing."""
from datetime import date
import logging
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

from .database import add_lead, lead_exists
from .messaging import draft_message
from .scoring import score_lead

LOG = logging.getLogger(__name__)
USER_AGENT = "NexoraLeadFinder/1.0 (public business research)"
EXCLUDED = {"linkedin.com", "facebook.com", "instagram.com", "x.com", "twitter.com", "youtube.com", "google.com", "clutch.co", "upwork.com"}
QUERIES = ('"software house"', 'SaaS company', '"web development agency"', 'ecommerce company', 'digital agency web applications')

def domain_key(url):
    parsed = urlparse(url if "://" in url else "https://" + url)
    return parsed.netloc.lower().split(":")[0].removeprefix("www.")

def _profile_url(soup, page_url):
    for link in soup.select("a[href]"):
        href = link["href"].lower()
        if "linkedin.com/company/" in href or "facebook.com/" in href:
            return urljoin(page_url, link["href"])[:500]
    return None

def _industry(text):
    low = text.lower()
    for phrase, label in (("e-commerce", "E-commerce"), ("ecommerce", "E-commerce"), ("web development", "Web development agency"), ("digital agency", "Digital agency"), ("saas", "SaaS"), ("software", "Software services")):
        if phrase in low: return label
    return "Small / medium business"

def _fetch_public_html(url):
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=12, allow_redirects=True)
        if response.ok and "text/html" in response.headers.get("content-type", "").lower():
            return response.url, response.text[:500_000], response.headers
    except requests.RequestException as exc:
        LOG.info("Could not read public page %s: %s", url, exc)
    return None, None, None


def public_recon(page_url, soup, headers, text):
    """Summarise publicly returned homepage information; never probes or scans a target."""
    title = (soup.title.string or "") if soup.title else ""
    description_tag = soup.select_one('meta[name="description"]')
    description = description_tag.get("content", "").strip()[:300] if description_tag else ""
    https_enabled = urlparse(page_url).scheme == "https"
    header_labels = {
        "strict-transport-security": "HSTS",
        "content-security-policy": "CSP",
        "x-content-type-options": "X-Content-Type-Options",
        "x-frame-options": "X-Frame-Options",
        "referrer-policy": "Referrer-Policy",
    }
    present_headers = [label for name, label in header_labels.items() if name in headers]
    technology_terms = (
        ("wordpress", "WordPress"), ("shopify", "Shopify"), ("woocommerce", "WooCommerce"),
        ("react", "React"), ("next.js", "Next.js"), ("cloudflare", "Cloudflare"),
        ("stripe", "Stripe"), ("google analytics", "Google Analytics"),
    )
    text_lower = text.lower()
    technologies = [label for phrase, label in technology_terms if phrase in text_lower]
    parts = ["HTTPS homepage" if https_enabled else "HTTP homepage"]
    if technologies:
        parts.append("public technology signals: " + ", ".join(technologies[:5]))
    if present_headers:
        parts.append("public response headers present: " + ", ".join(present_headers))
    return {
        "site_title": title.strip()[:200] or None,
        "site_description": description or None,
        "https_enabled": int(https_enabled),
        "security_headers": ", ".join(present_headers) or "None observed on homepage response",
        "technology_signals": ", ".join(technologies[:5]) or "No common technology signal identified",
        "recon_summary": ". ".join(parts) + ".",
    }

def discover_leads(con, limit=10, location=None):
    """Discover a maximum of ten new domains and store them locally."""
    new, seen = [], set()
    try:
        with DDGS() as search:
            results = []
            for query in QUERIES:
                results.extend(search.text(f"{query} {location or ''}".strip(), max_results=10))
    except Exception as exc:
        LOG.error("Public search failed: %s", exc)
        return new
    for result in results:
        if len(new) >= limit: break
        url = result.get("href") or result.get("url")
        key = domain_key(url or "")
        if not key or key in EXCLUDED or key in seen or lead_exists(con, key): continue
        seen.add(key)
        final_url, html, headers = _fetch_public_html(url)
        if not html: continue
        key = domain_key(final_url)
        if not key or lead_exists(con, key): continue
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)[:40_000]
        title = (soup.title.string or key) if soup.title else key
        site_name = soup.select_one("meta[property='og:site_name']")
        company = (site_name.get("content") if site_name else title.split("|")[0].split("-")[0]).strip()[:120]
        industry = _industry(text + " " + (result.get("body") or ""))
        score, reason = score_lead(text, industry)
        recon = public_recon(final_url, soup, headers, text)
        address = re.search(r"(?:Address|Office|Location)\s*[:\-]?\s*([^|]{5,100})", text, re.I)
        lead = {"company_name": company, "website": final_url, "website_key": key, "industry": industry,
                "location": (address.group(1).strip() if address else location or "Not publicly identified")[:160],
                "profile_url": _profile_url(soup, final_url), "security_reason": reason, "lead_score": score,
                "outreach_message": draft_message(company, reason, recon["recon_summary"]), "status": "New", "discovered_on": date.today().isoformat(),
                "source_url": url, "notes": None, **recon}
        add_lead(con, lead); new.append(lead)
    return new
