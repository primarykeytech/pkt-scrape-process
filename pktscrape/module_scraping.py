"""Legacy Selenium adapter, kept separate from the offline default demo."""

from urllib.parse import urlparse

from bs4 import BeautifulSoup
from selenium import webdriver

from .models import Experience
from .sources import approved_links

__all__ = ["Experience", "ScrapeSite"]


class ScrapeSite:
    """Bounded browser collector for an explicitly approved single host."""

    def __init__(self, *, driver=None, max_pages: int = 50):
        self.links: list[str] = []
        self.driver = driver
        self.max_pages = max_pages

    def create_driver(self) -> None:
        if self.driver is None:
            self.driver = webdriver.Firefox()

    def quit_driver(self) -> None:
        if self.driver is not None:
            self.driver.quit()
            self.driver = None

    def scrape_page(self, url: str) -> BeautifulSoup:
        self.create_driver()
        self.driver.set_page_load_timeout(30)
        self.driver.get(url)
        requested = urlparse(url)
        final_url = getattr(self.driver, "current_url", url)
        final = urlparse(final_url)
        if final.scheme not in {"http", "https"} or final.hostname != requested.hostname:
            raise ValueError("Browser navigation left the approved host")
        self._last_page_url = final_url
        return BeautifulSoup(self.driver.page_source, "html.parser")

    def get_page_links(self, url: str, must_contain: str = "") -> list[str]:
        """Extract links from one page; never recurses or leaves the starting host."""
        try:
            return approved_links(str(self.scrape_page(url)), page_url=self._last_page_url, required_text=must_contain,
                                  allowed_host=urlparse(url).hostname or "")
        finally:
            self.quit_driver()

    def crawl_for_links(self, url: str, must_contain: str = "") -> list[str]:
        """Breadth-first crawl with a host boundary and a hard page limit."""
        allowed_host = urlparse(url).hostname or ""
        queue = [url]
        self.links = []
        try:
            while queue and len(self.links) < self.max_pages:
                page = queue.pop(0)
                if page in self.links:
                    continue
                self.links.append(page)
                page_links = approved_links(str(self.scrape_page(page)), page_url=self._last_page_url,
                                            required_text=must_contain, allowed_host=allowed_host)
                queue.extend(link for link in page_links if link not in self.links and link not in queue)
            return self.links
        finally:
            self.quit_driver()
