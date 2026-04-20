def google_cse_find_site(query: str, api_key: str, cx: str, num: int = 5, pause: float = 1.2) -> list[str]:
    """
    Query Google Custom Search JSON API and return a list of result URLs.
    - api_key: GOOGLE_API_KEY
    - cx: GOOGLE_CX (Programmable Search Engine ID)
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": api_key, "cx": cx, "q": query, "num": min(max(num, 1), 10)}
    r = requests.get(url, params=params, timeout=12)
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


def find_emails_for_website(url: str) -> list[str]:
    """Find emails for a given website by crawling homepage + contact pages."""
    html = fetch_html(url)
    emails = extract_emails_from_html(html)
    if emails:
        return emails

    # try contact/about pages
    emails = try_contact_pages(url)
    if emails:
        return emails

    # fallback: crawl some internal links
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
        if cl in tried:
            continue
        tried.add(cl)
        html = fetch_html(cl)
        found = extract_emails_from_html(html)
        if found:
            return found
    return []