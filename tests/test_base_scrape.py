from pktscrape.module_scraping import ScrapeSite
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cfg

def base_page_links():
    scraped = ScrapeSite()
    scraped_links = scraped.get_page_links(cfg.BASE_URL,
                                          cfg.BASE_MUST_CONTAIN)
    return scraped_links

def test_base_page_links_result():
    links = base_page_links()
    assert len(links) > 0

def single_page_links():
    scraped = ScrapeSite()
    scraped_links = scraped.get_page_links(
        cfg.TEST_SINGLE_PAGE_URL, cfg.PAGE_MUST_CONTAIN)
    return scraped_links

def test_single_page_links_result():
    links = single_page_links()
    assert len(links) > 0

def single_page_content():
    scraped = ScrapeSite()
    scraped_content = scraped.get_page_content(
        cfg.TEST_SINGLE_PAGE_CONTENT)
    return scraped_content.find('p', {"align": "left"})

def test_single_page_content_result():
    content = single_page_content()
    assert len(content) > 0

