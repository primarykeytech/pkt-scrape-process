import pytest
from bs4 import BeautifulSoup

# from pktscrape.module_scraping import ScrapeSite
from pktscrape.pktscrape import (extract_experience,
                                 experience_objects_from_list)
import pktscrape.helpers
import cfg


def test_strip_html():
    # test the strip_html function.
    assert pktscrape.helpers.strip_html('<p>hello</p>') == 'hello'


def test_extract_experience():
    """
    Test the extract_experience function.
    """
    # create a mock content string.
    mock_content = f"""<div class='{cfg.IDENTIFY_CONTENT}'>test1</div>
            <div class='{cfg.IDENTIFY_CONTENT}'>test2</div>"
            <div class='{cfg.IDENTIFY_CONTENT}'>test3</div>"""

    # create a beautifulsoup object.
    soup = BeautifulSoup(mock_content, "html.parser")

    # run the function.
    list_content = extract_experience(soup)

    # test the result.
    assert len(list_content) == 3

    list_exp_obj = experience_objects_from_list(list_content)

    assert len(list_exp_obj) == 3
    assert list_exp_obj[0].description == 'test1'


def test_scrape_links():
    pass


# def test_scrape_links():
#     # create the scrapesite object.
#     scraped = ScrapeSite()
#     # get the links on the page set the in the cfg file as a list.
#     scraped_links = scraped.get_page_links(cfg.BASE_URL,
#                                            cfg.BASE_MUST_CONTAIN)
#     # run the test.
#     assert len(scraped_links) > 0
#
#
# def test_single_page_links_result():
#     scraped = ScrapeSite()
#     scraped_links = scraped.get_page_links(
#         cfg.TEST_SINGLE_PAGE_URL, cfg.PAGE_MUST_CONTAIN)
#     assert len(scraped_links) > 0
#
#
# def single_page_content():
#     scraped = ScrapeSite()
#     scraped_content = scraped.get_page_content(
#         cfg.TEST_SINGLE_PAGE_CONTENT)
#     return scraped_content.find('p', {"align": "left"})
#
#
# def test_single_page_content_result():
#     #create scrape object.
#     scraped = ScrapeSite()
#
#     # get beautifulsoup object.
#     scraped_content = scraped.get_page_content(
#         cfg.TEST_SINGLE_PAGE_CONTENT)
#
#     # count the number of elements with the
#     count_element = len(scraped_content.find_all(cfg.WEB_TYPE_OF_ELEMENT,
#                                                  {"class": cfg.WEB_ELEMENT_TO_WAIT}))
#
#     # test if the value set in cfg is in the html string.
#     assert count_element > 0
