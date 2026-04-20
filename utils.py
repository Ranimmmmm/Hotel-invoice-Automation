import csv
from config import OUTPUT_LOG


def init_log():
    """Initialize the log file with headers."""
    with open(OUTPUT_LOG, 'w', newline='', encoding='utf-8') as logf:
        writer = csv.writer(logf)
        writer.writerow([
            'row_index', 'hotel', 'client', 'duration',
            'website', 'emails', 'status', 'notes'
        ])
import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import BLACKLIST_DOMAINS, REQUEST_HEADERS, CONTACT_PATHS as CFG_CONTACT_PATHS

# =============== Email regex & constants ===============
EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
CONTACT_PATHS = CFG_CONTACT_PATHS


# =============== Utils ===============
# Create a shared Session with sane retries to avoid long hangs
_def_retry = Retry(
    total=2,
    connect=2,
    read=2,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "HEAD"],
    raise_on_status=False,
)
_session = requests.Session()
adapter = HTTPAdapter(max_retries=_def_retry, pool_connections=10, pool_maxsize=10)
_session.mount("http://", adapter)
_session.mount("https://", adapter)


def is_blacklisted(url: str) -> bool:
    if not url:
        return True
    return any(domain in url for domain in BLACKLIST_DOMAINS)


def fetch_html(url: str, timeout: tuple[int, int] | int = (5, 10)) -> str | None:
    """Fetch raw HTML for a given URL with short timeouts and retries.

    timeout: either a single seconds value or (connect, read)
    """
    try:
        resp = _session.get(url, timeout=timeout, headers=REQUEST_HEADERS)
        if resp.status_code == 200 and 'text' in (resp.headers.get('Content-Type') or ''):
            return resp.text
    except Exception:
        return None
    return None


# =============== Google Custom Search JSON API ===============
def google_cse_find_site(query: str, api_key: str, cx: str, num: int = 5, pause: float = 1.2) -> list[str]:
    """
    Query Google Custom Search JSON API and return a list of result URLs.
    - api_key: GOOGLE_API_KEY
    - cx: GOOGLE_CX (Programmable Search Engine ID)
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": api_key, "cx": cx, "q": query, "num": min(max(num, 1), 10)}
    r = _session.get(url, params=params, timeout=(5, 10))
    r.raise_for_status()
    data = r.json()
    links: list[str] = []
    for item in data.get("items", []) or []:
        link = item.get("link")
        if link:
            links.append(link)
    time.sleep(pause)
    return links


# =============== Email extraction ===============
def extract_emails_from_html(html: str | None) -> list[str]:
    """Extract emails from raw HTML (anchors + plain text)."""
    if not html:
        return []
    emails = set()
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    # mailto: links
    for a in soup.select('a[href^="mailto:"]'):
        href = a.get("href")
        if href:
            m = EMAIL_REGEX.search(href)
            if m:
                emails.add(m.group(0))

    # plain text emails
    for m in EMAIL_REGEX.finditer(soup.get_text()):
        emails.add(m.group(0))

    return list(emails)


def try_contact_pages(base_url: str) -> list[str]:
    """Try common contact/about pages for emails."""
    emails: list[str] = []
    for p in CONTACT_PATHS:
        candidate = urljoin(base_url, p)
        html = fetch_html(candidate)
        if html:
            found = extract_emails_from_html(html)
            if found:
                emails.extend(found)
    return list(set(emails))


def find_emails_for_website(url: str, max_seconds: float = 20.0) -> list[str]:
    """Find emails for a given website by crawling homepage + contact pages with a time budget."""
    start_time = time.time()

    def _time_left() -> bool:
        return (time.time() - start_time) < max_seconds

    if not _time_left():
        return []

    html = fetch_html(url)
    emails = extract_emails_from_html(html)
    if emails:
        return emails

    # try contact/about pages
    if not _time_left():
        return []
    emails = try_contact_pages(url)
    if emails:
        return emails

    # fallback: crawl some internal links
    if not _time_left():
        return []
    try:
        base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    except Exception:
        return []

    home_html = fetch_html(base)
    if not home_html:
        return []

    soup = BeautifulSoup(home_html, "lxml")
    anchors = soup.find_all("a", href=True)
    candidate_links: list[str] = []
    for a in anchors:
        href = a["href"]
        if href.startswith("/"):
            candidate_links.append(urljoin(base, href))
        elif base in href:
            candidate_links.append(href)

    tried = set()
    for cl in candidate_links[:8]:  # only check first 8 internal links
        if not _time_left():
            break
        if cl in tried:
            continue
        tried.add(cl)
        html = fetch_html(cl)
        found = extract_emails_from_html(html)
        if found:
            return found
    return []


def log_result(idx, hotel, client, duration, website, emails, status, notes):
    """Append a result line to the log file."""
    with open(OUTPUT_LOG, 'a', newline='', encoding='utf-8') as logf:
        writer = csv.writer(logf)
        writer.writerow([
            idx,
            hotel,
            client,
            duration,
            website,
            ';'.join(emails) if emails else '',
            status,
            notes
        ])
