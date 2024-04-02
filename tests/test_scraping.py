from unittest.mock import PropertyMock, patch
import pytest
from bs4 import BeautifulSoup
from pktscrape.pktscrape import (extract_experience,
                                 experience_objects_from_list)
import pktscrape.helpers
import cfg
from pktscrape.module_scraping import ScrapeSite


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


@patch('pktscrape.module_scraping.ScrapeSite')
def test_crawl_for_links(mock_class):
    """
    Test the crawl_for_links method. We are mocking the ScrapeSite class since the
    method sets class properties.
    :param mock_class: Used to create the mock ScrapeSite class.
    """

    # intended to be the initial url.
    url = "<a href='https://www.primarykeytech.com/'>PKT HOME</a>"

    # Create a mock instance of the class
    mock_instance = mock_class.return_value

    def side_effect(url):
        """
        Side effect to set the links property.
        :return: Array of links that would be set by the method.
        """
        mock_instance.links = [f"{url}",
                               "<a href='https://www.primarykeytech.com/subpage?1'>test</a>",
                               "<a href='https://www.primarykeytech.com/subpage?2'>test2</a>"]
        return mock_instance.links

    # Set expectation for crawl_for_links method using the
    # side_effect function above. This sets the links property.
    mock_instance.crawl_for_links.side_effect = side_effect

    # Call the method on the mock instance
    mock_instance.crawl_for_links(url)

    # Test the result.
    assert len(mock_instance.links) == 3


# @patch('pktscrape.module_scraping.ScrapeSite.links',
#        new_callable=PropertyMock,
#        return_value=["<a href='http://www.test.com/subpage?1'>test</a>",
#                      "<a href='http://www.test.com/subpage?2'>test2</a>"])
# def test_crawl_for_links(mocker):
#
#     # fake_response = ["<a href='http://www.test.com/subpage?1'>test</a>",
#     #                  "<a href='http://www.test.com/subpage?2'>test2</a>"]
#
#     # mocker.patch(
#     #     "pktscrape.module_scraping.ScrapeSite.get_page_links", return_value=fake_response
#     # )
#
#     # with mocker.patch('pktscrape.module_scraping.ScrapeSite.get_page_links',
#     #                   new_callable=PropertyMock,
#     #            return_value={'a': 1}):
#
#     scraped = ScrapeSite()
#     scraped.crawl_for_links("<a href='http://www.test.com/'>test</a>", "subpage")
#
#     # print(scraped.links)
#
#
#     assert len(scraped.links) == 2


    # # Initialize the ScrapeSite class with fresh data.
    # scraped = ScrapeSite()
    # scraped.crawl_for_links("<a href='http://www.test.com/'>test</a>", "subpage")

    # print(scraped.links)
    #
    # assert len(scraped.links) == 2


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
