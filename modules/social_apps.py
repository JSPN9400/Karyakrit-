"""
Social media and messaging helpers.
"""

import urllib.parse
import webbrowser


SOCIAL_URLS = {
    "whatsapp": "https://web.whatsapp.com/",
    "linkedin": "https://www.linkedin.com/",
    "linkedin jobs": "https://www.linkedin.com/jobs/",
    "github": "https://github.com/",
    "instagram": "https://www.instagram.com/",
    "facebook": "https://www.facebook.com/",
    "x": "https://x.com/",
    "twitter": "https://x.com/",
    "youtube": "https://www.youtube.com/",
}


def open_social(target: str) -> str:
    """Open a known social or messaging destination."""
    key = target.strip().lower()
    url = SOCIAL_URLS.get(key)
    if not url:
        return f"Social target not configured: {target}"
    webbrowser.open(url)
    return f"Opened {target}: {url}"


def search_linkedin_jobs(query: str) -> str:
    """Open LinkedIn jobs search results."""
    encoded = urllib.parse.quote_plus(query.strip())
    url = f"https://www.linkedin.com/jobs/search/?keywords={encoded}"
    webbrowser.open(url)
    return f"Opened LinkedIn job search for: {query}"
