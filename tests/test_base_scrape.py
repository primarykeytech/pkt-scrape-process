from pktscrape.module_scraping import ScrapeSite
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# import ../db.py
import cfg

def test_one():
    scraped = ScrapeSite(cfg.BASE_URL)
    scraped_text = scraped.get_base_page()
    return scraped_text

def test_answer():
    obj = test_one()
    print(obj)
    assert len(obj) > 0

