from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
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

    @staticmethod
    def scrape_page(url):
        """
        Use selenium to scrape the page.
        :param url: URL of page to scrape.
        :return: List of links from the page.
        """
        # list to hold the links pulled from the page.
        archive_links = []

        # open the page with selenium.
        with webdriver.Firefox() as driver:
            time.sleep(3)  # seems to work better with a slight wait
            driver.get(url)
            scrape_response = driver.page_source
            archive_links = BeautifulSoup(scrape_response, 'html.parser')
            driver.quit()

        # return the links.
        return archive_links

    def get_page_links(self, url, must_contain=""):
        """
        Scrapes the page specified upon. Uses
        selenium since the test site that I used had blocked
        vanilla scraping.
        :return: links contained on the base page.
        """
        print('In get_page_links...')

        # list to hold cleaned up links.
        links_return = []

        # open the page with selenium.
        archive_links = self.scrape_page(url)

        # loop through just the links on the page.
        for link in archive_links.findAll('a', href=True):

            print(f'Evaluating {link}')

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

                    # recursively call this function to get the links on the page.
                    self.get_page_links(the_link, must_contain)

    @staticmethod
    def get_page_content(url):
        """
        Scrapes all the HTML from a specified URL.
        :param url: The full URL of the page.
        :return: A BeautifulSoup object.
        """

        # string to hold response from scraping.
        scrape_response = ""

        # content parsed into beautiful soup.
        bs_content = ""

        # try to connect to the site using selenium and firefox.
        try:
            # create the firefox driver.
            driver = webdriver.Firefox()
            # seems to work better with a slight wait
            # time.sleep(3)

            # get the page content.
            driver.get(url)

            # see if the config file has a delay set.
            # if there is a delay, we will be waiting for an element with a
            # particular class name to appear.
            if cfg.WEB_DELAY > 0:
                WebDriverWait(driver, 20) \
                    .until(EC.visibility_of_element_located((By.CLASS_NAME,
                                                             cfg.WEB_ELEMENT_TO_WAIT)))

            # set the response.
            scrape_response = driver.page_source

            # parse the text with beautiful soup.
            bs_content = BeautifulSoup(scrape_response, 'html.parser')
        except:
            # report error.
            print("driver failed")
        finally:
            # close the browser window.
            driver.quit()

        # return the beautiful soup object.
        return bs_content

    def crawl_for_links(self, url, must_contain=""):
        """
        Crawls the site for links.
        :param url: The URL to use as the starting point.
        :param must_contain: The string that must be in the link.
        :return: A list of links from the page.
        """
        print("Starting crawl for links...")

        # list to hold the links pulled from the page.
        self.links = [url]

        self.get_page_links(url, must_contain)

        # # open the page with selenium.
        # with webdriver.Firefox() as driver:
        #     time.sleep(3)
