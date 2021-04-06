from module_scraping import ScrapeSite, Experience
import uuid
from module_db import DynamoDb
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cfg


def create_experience_obj(bs_content):
    """
    Takes an input HTML string and turns it into an Experience
    object. This will likely need to be changed depending on the
    source of the scraped data.

    :param bs_content: HTML string.
    :return: Experience object.
    """
    # create experience obj
    objExp = Experience()

    # generate random id.
    objExp.uuid = str(uuid.uuid1())

    # extract the title.
    objExp.title = bs_content.h1.get_text()

    # get li's from breadcrumbs
    list_ul = bs_content.find('ul', class_="breadcrumbs")
    list_li = list_ul.find_all('li')

    # loop through list items to find classification.
    for li in list_li:
        # extract text and clean up.
        li_text = li.get_text()
        if "Classification" in li_text:
            objExp.classification = li_text.replace("Classification ", "")

    # get the main content which is always in p tag with
    # left alignment.
    content_area = bs_content.find('p', {"align": "left"})
    if content_area is None:
        objExp.description = " "
    else:
        objExp.description = content_area.get_text()

    # return the object.
    return objExp


def scrape_experiences():
    """
    Scrapes the content from the specified url. This function
    will likely need to be adjusted depending on the source
    of your data. Saves the scraped record in a dynamo db
    database after creating objects from HTML strings.
    """

    print("Starting the scraping process...")

    # create the obj to begin scraping.
    obj = ScrapeSite()

    # get the links from the base page.
    print("Getting base page links...")
    top_links = obj.get_page_links(cfg.BASE_URL,
                                   cfg.BASE_MUST_CONTAIN)
    print("Retrieved ", str(len(top_links)), " base page links.")

    # to count which link we are on.
    count_top = 0

    # loop through base page links.
    # for link in top_links:
    for link in top_links[8:]:
        # increment count.
        count_top += 1

        print("Processing page ", str(count_top),
              " of ", str(len(top_links)))

        # get the links on the child page.
        links_single_page = obj.get_page_links(
            link, cfg.PAGE_MUST_CONTAIN)

        # process links on child page.
        for page_link in links_single_page:

            # get the content of the page as a beautiful
            # soup object.
            bs_content = obj.get_page_content(page_link)

            # create the experience object.
            obj_exp = create_experience_obj(bs_content)

            # create the dynamodb object and add record.
            print("Adding: ", obj_exp.title)
            obj_db = DynamoDb()
            obj_db.create_record(obj_exp)

# start the process.
scrape_experiences()

