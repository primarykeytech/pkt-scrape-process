import pytest
from pktscrape.module_scraping import ScrapeSite
import cfg


def test_scrape_links():
    # create the scrapesite object.
    scraped = ScrapeSite()
    # get the links on the page set the in the cfg file as a list.
    scraped_links = scraped.get_page_links(cfg.BASE_URL,
                                           cfg.BASE_MUST_CONTAIN)
    # run the test.
    assert len(scraped_links) > 0


def test_single_page_links_result():
    scraped = ScrapeSite()
    scraped_links = scraped.get_page_links(
        cfg.TEST_SINGLE_PAGE_URL, cfg.PAGE_MUST_CONTAIN)
    assert len(scraped_links) > 0


def single_page_content():
    scraped = ScrapeSite()
    scraped_content = scraped.get_page_content(
        cfg.TEST_SINGLE_PAGE_CONTENT)
    return scraped_content.find('p', {"align": "left"})


def test_single_page_content_result():
    #create scrape object.
    scraped = ScrapeSite()

    # get beautifulsoup object.
    scraped_content = scraped.get_page_content(
        cfg.TEST_SINGLE_PAGE_CONTENT)

    # count the number of elements with the
    count_element = len(scraped_content.find_all(cfg.WEB_TYPE_OF_ELEMENT,
                                                 {"class": cfg.WEB_ELEMENT_TO_WAIT}))

    # test if the value set in cfg is in the html string.
    assert count_element > 0
