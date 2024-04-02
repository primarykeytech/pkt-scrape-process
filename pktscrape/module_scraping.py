from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import cfg


class Experience:
    """
    Objects created with the Experience class will be used
    to save the content in DynamoDB.
    """

    def __init__(self):
        self.uuid = ""
        self.title = ""
        self.classification = ""
        self.description = ""


class ScrapeSite:
    """
    ScrapeSite handles all the site scraping and cleaning
    of data related to the scraping.
    """

    def __init__(self):
        self.links = []
        self.driver = webdriver.Firefox()

    def create_driver(self):
        """
        Creates a new Firefox driver.
        :return: None
        """
        self.driver = webdriver.Firefox()

    def quit_driver(self):
        """
        Quits the Firefox driver.
        :return: None
        """
        self.driver.quit()

    def scrape_page(self, url):
        """
        Use selenium to scrape the page.
        :param url: URL of page to scrape.
        :return: List of links from the page.
        """
        self.driver.get(url)
        scrape_response = self.driver.page_source
        archive_links = BeautifulSoup(scrape_response, 'html.parser')

        # return the links.
        return archive_links

    def get_page_links(self, url, must_contain=""):
        """
        Recursive function that scrapes the page specified upon.
        Uses selenium since the test site that I used had blocked scraping.
        :return: links contained on the base page.
        """

        # list to hold cleaned up links.
        links_return = []

        # open the page with selenium.
        archive_links = self.scrape_page(url)

        # loop through just the links on the page.
        for link in archive_links.findAll('a', href=True):

            # use value stored in config file to determine if
            # this is a link that we want. This will vary depending
            # on the page from which we scrape.
            if must_contain in link['href']:
                # set the link.
                the_link = link['href']

                # if the link is not a full URL, add the base URL.
                if 'http' not in the_link:
                    the_link = cfg.HOME_URL + the_link

                # check if the link is already in the list
                # to return.
                if the_link not in self.links:

                    print(f'Adding {the_link} to the list...')

                    # add to the list.
                    self.links.append(the_link)

                    # recursion to get all the links from all the pages.
                    self.get_page_links(the_link, must_contain)

    def crawl_for_links(self, url, must_contain=""):
        """
        Crawls the site for links.
        :param url: The URL to use as the starting point.
        :param must_contain: The string that must be in the link.
        :return: A list of links from the page.
        """

        # list to hold the links pulled from the page.
        # start with the base URL.
        self.links = [url]
        self.get_page_links(url, must_contain)
