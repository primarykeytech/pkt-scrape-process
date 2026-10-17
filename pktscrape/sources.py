"""Approved content sources.

The default demo source is intentionally offline.  Live browser collection is an
opt-in adapter and callers must supply the source policy explicitly.
"""

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .models import Experience


class OfflineHtmlSource:
    """Extract typed records from supplied HTML; it never performs network I/O."""

    def __init__(self, html: str, *, classification: str, content_class: str, title: str):
        self.html = html
        self.classification = classification
        self.content_class = content_class
        self.title = title

    def experiences(self) -> list[Experience]:
        soup = BeautifulSoup(self.html, "html.parser")
        return [
            Experience.create(
                title=f"{index} - {self.title}",
                classification=self.classification,
                description=element.get_text(" ", strip=True),
            )
            for index, element in enumerate(soup.find_all("div", class_=self.content_class), start=1)
            if element.get_text(" ", strip=True)
        ]


def approved_links(html: str, *, page_url: str, required_text: str, allowed_host: str) -> list[str]:
    """Return de-duplicated links on one page, constrained to an approved host."""
    links: list[str] = []
    for anchor in BeautifulSoup(html, "html.parser").find_all("a", href=True):
        link = urljoin(page_url, anchor["href"])
        parsed = urlparse(link)
        if parsed.hostname == allowed_host and required_text in link and link not in links:
            links.append(link)
    return links
