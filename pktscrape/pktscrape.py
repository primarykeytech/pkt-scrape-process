from module_scraping import ScrapeSite, Experience

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cfg



obj = ScrapeSite()

"""
top_links = obj.get_page_links(cfg.BASE_URL, cfg.BASE_MUST_CONTAIN)
print("printing top links...")
print(top_links)

for link in top_links[:1]:
    links_single_page = obj.get_page_links(link, cfg.PAGE_MUST_CONTAIN)
    print("SINGLE PAGE LINKS")
    print(links_single_page)

    for page_link in links_single_page[:1]:
"""

#bs_content = obj.get_page_content(page_link)
bs_content = \
    obj.get_page_content(
        'https://www.nderf.org/Experiences/1alfred_a_nde.html')

# create experience obj
objExp = Experience()
objExp.title = bs_content.h1.get_text()
print(objExp.title)
# get li's from breadcrumbs
list_ul = bs_content.find('ul', class_="breadcrumbs")

list_li = list_ul.find_all('li')

for li in list_li:
    li_text = li.get_text()
    if "Classification" in li_text:
        print(li_text.replace("Classification ", ""))
        obj.classification = li_text.replace("Classification ", "")

content_area = bs_content.find('p', {"align": "left"})
objExp.description = content_area.get_text()

print(objExp.description)
