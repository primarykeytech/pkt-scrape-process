from bs4 import BeautifulSoup
from selenium import webdriver
import time


import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# import ../db.py
import cfg

class ScrapeSite:
    def __init__(self, base_url):
        self.base_url = base_url

    def get_base_page(self):

        scrape_response = ""
        archive_links = []
        links_return = []

        try:
            driver = webdriver.Firefox(executable_path='drivers/geckodriver')
            # seems to work better with a slight wait
            # driver.implicitly_wait(20)
            time.sleep(3)
            driver.get(self.base_url)
            scrape_response = driver.page_source
            # driver.quit()
        except:
            print("driver failed")

        #archive_links = driver.find_elements_by_tag_name('a')
        #archive_links = driver.find_elements_by_xpath("//a[@href]")
        archive_links = BeautifulSoup(scrape_response, 'html.parser')
        driver.quit()
        #driver.close()
        #soup = BeautifulSoup(scrape_response, 'html.parser')
        # soup = BeautifulSoup(self.base_url, 'html.parser')
        #return soup.prettify()
        for link in archive_links.findAll('a', href=True):

            if '/Archives/' in link['href']:
                the_link = link['href']
                print("the_link", the_link)
                if the_link not in links_return:
                    links_return.append(the_link)

        return links_return


obj = ScrapeSite(cfg.BASE_URL)
links = obj.get_base_page()
print("print links...")
for link in links:
    print(link)
