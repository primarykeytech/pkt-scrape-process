from module_scraping import ScrapeSite, Experience
import uuid
from module_db import DynamoDb
import os
import sys
import cfg
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def extract_experience(bs_content):
    """
    Extracts the experience from the content of the page.
    This will likely need to be adjusted depending on the
    source of the scraped data.

    :param bs_content: HTML string.
    :return: Experience object.
    """
    list_content = []

    if cfg.IDENTIFY_BY == "class":
        list_content = bs_content.find_all('div', cfg.IDENTIFY_CONTENT)

    print(f"Found {str(len(list_content))} content items.")

    # list to return
    list_return = []

    # loop through list content and process text before adding to return list.
    for item in list_content:

        # extract text and clean up.
        item_from_get_text = item.get_text(strip=True)
        list_return.append(item_from_get_text)

    return list_return


def create_experience_obj(bs_content):
    """
    Takes an input HTML string and turns it into an Experience
    object. This will likely need to be changed depending on the
    source of the scraped data.

    :param bs_content: HTML string.
    :return: list of strings
    """
    # create experience obj
    exp = Experience()

    # generate random id.
    exp.uuid = str(uuid.uuid1())

    # # extract the title.
    # exp.title = bs_content.h1.get_text()
    #
    # # get li's from breadcrumbs
    # list_ul = bs_content.find('ul', class_="breadcrumbs")
    # list_li = list_ul.find_all('li')

    list_content = []

    if cfg.IDENTIFY_BY == "class":
        list_content = bs_content.find_all('div', cfg.IDENTIFY_CONTENT)

    print(f"Found {str(len(list_content))} content items.")

    # loop through list content and process text before adding to return list.
    for item in list_content:

        # extract text and clean up.
        item_from_get_text = item.get_text(strip=True)

        # item_text = item_text.strip()
        # print(item_from_get_text)
        # print("\n\n")




    # # loop through list items to find classification.
    # for li in list_li:
    #     # extract text and clean up.
    #     li_text = li.get_text()
    #     if "Classification" in li_text:
    #         exp.classification = li_text.replace("Classification ", "")
    #
    # # get the main content which is always in p tag with
    # # left alignment.
    # content_area = bs_content.find('p', {"align": "left"})
    # if content_area is None:
    #     exp.description = " "
    # else:
    #     exp.description = content_area.get_text()

    # return the object.
    return exp


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
    # include the base page.
    top_links.append(cfg.BASE_URL)
    print("Retrieved ", str(len(top_links)), " base page links.")

    # to count which link we are on.
    count_top = 0

    # loop through base page links.
    # for link in top_links:
    for link in top_links:
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
            # bs_content = obj.get_page_content(page_link)
            bs_content = obj.scrape_page(page_link)

            # create the experience object.
            obj_exp = create_experience_obj(bs_content)

            # create the dynamodb object and add record.
            print("Adding: ", obj_exp.title)
            obj_db = DynamoDb()
            obj_db.create_record(obj_exp)


# alternate scrape
# crawl pages to gather links.
# loop through pages and scrape content.
# create experience objects.
# save to dynamodb.
def scrape_experience_alternate():
    """
    Scrapes and chooses the links, then the content, then
    creates the objects, and finally saves to dynamodb.
    """

    print("Scraping the links...")

    # create the obj to begin scraping.
    obj = ScrapeSite()

    # create a selenium driver to share.
    obj.create_driver()

    # crawl the site for links starting at the base page.
    obj.crawl_for_links(cfg.BASE_URL, cfg.BASE_MUST_CONTAIN)

    print(obj.links)

    # list to hold experience objects.
    list_exp = []

    # iterate through the links and scrape the content.
    for link in obj.links:

        print(f"Scraping content from {link}...")
        bs_content = obj.scrape_page(link)

        # extract the experiences from the page content and add to the list.
        list_exp.extend(extract_experience(bs_content))

    # close the driver.
    obj.quit_driver()
    print(f"Scraped {str(len(list_exp))} experience objects.")

    # list for experience objects.
    list_exp_obj = []

    # simple counter.
    count = 0

    # loop through the list of experiences and create objects.
    for exp in list_exp:
        obj_exp = Experience()
        obj_exp.uuid = str(uuid.uuid1())
        obj_exp.classification = cfg.CLASSIFICATION
        obj_exp.title = f"{str(count)} - {cfg.BASE_URL}"
        obj_exp.description = exp
        list_exp_obj.append(obj_exp)
        count += 1

    # create the dynamodb object.
    obj_db = DynamoDb()
    db_success = obj_db.create_multiple_records(list_exp_obj)

    print(f'db_success: {db_success}')


# start the process.
# scrape_experiences()
start_time = time.time()
scrape_experience_alternate()
print("--- %s seconds ---" % (time.time() - start_time))
