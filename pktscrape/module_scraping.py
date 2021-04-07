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
    ScrapeSite handles all of the site scraping and cleaning
    of data related to the scraping.
    """
    # TODO: abstract out actual scraping code.

    def __init__(self):
        pass

    def get_page_links(self, url, must_contain = ""):
        """
        Scrapes the page specified upon. Uses
        selenium since the test site that I used had blocked
        vanilla scraping.
        :return: links contained on the base page.
        """
        # string to hold response from scraping.
        scrape_response = ""
        # list to hold the links pulled from the page.
        archive_links = []
        # list to hold cleaned up links.
        links_return = []

        # try to connect to the site using selenium and firefox.
        try:
            driver = webdriver.Firefox(executable_path='drivers/geckodriver')
            # seems to work better with a slight wait
            time.sleep(3)
            driver.get(url)
            # set the response.
            scrape_response = driver.page_source
            # parse the text with beautiful soup.
            archive_links = BeautifulSoup(scrape_response, 'html.parser')
        except:
            # report error.
            print("driver failed")
        finally:
            # close the browser window.
            driver.quit()

        # loop through just the links on the page.
        for link in archive_links.findAll('a', href=True):
            # use value stored in config file to determine if
            # this is a link that we want. This will vary depending
            # on the page from which we scrape.
            if must_contain in link['href']:
                # set the link.
                the_link = link['href']
                # check if the link is already in the list
                # to return.
                if the_link not in links_return:
                    # add to the list.
                    links_return.append(the_link)
        # return the cleaned up list.
        return links_return

    def get_page_content(self, url):
        """
        Scrapes all of the HTML from a specified URL.
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
            driver = webdriver.Firefox(executable_path='drivers/geckodriver')
            # seems to work better with a slight wait
            # time.sleep(3)

            # get the page content.
            driver.get(url)

            # see if the config file has a delay set.
            # if there is a delay, we will be waiting for an element with a
            # particular class name to appear.
            if cfg.WEB_DELAY > 0:
                WebDriverWait(driver, 20)\
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

