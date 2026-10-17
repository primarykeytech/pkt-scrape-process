from bs4 import BeautifulSoup

import cfg
from fixtures import data_table
from pktscrape.module_scraping import ScrapeSite
from pktscrape.models import Experience
from pktscrape.pktscrape import create_experience_obj
from pktscrape.storage import DynamoExperienceRepository


class FakeDriver:
    def __init__(self, pages):
        self.pages = pages
        self.page_source = ""
        self.current_url = ""
        self.timeout = None
        self.quit_called = False

    def set_page_load_timeout(self, seconds):
        self.timeout = seconds

    def get(self, url):
        self.page_source = self.pages[url]
        self.current_url = url

    def quit(self):
        self.quit_called = True


def test_get_page_links_returns_same_host_matches_and_sets_timeout():
    page = "https://example.test/root"
    driver = FakeDriver({
        page: '<a href="/entry?ok">one</a><a href="https://other.test/entry?ok">bad</a>',
    })

    links = ScrapeSite(driver=driver).get_page_links(page, "?ok")

    assert links == ["https://example.test/entry?ok"]
    assert driver.timeout == 30


def test_crawl_respects_host_boundary_and_page_cap():
    root = "https://example.test/root"
    first = "https://example.test/first?ok"
    driver = FakeDriver({
        root: f'<a href="{first}">first</a><a href="https://other.test/out?ok">out</a>',
        first: '<a href="/second?ok">second</a>',
    })

    links = ScrapeSite(driver=driver, max_pages=2).crawl_for_links(root, "?ok")

    assert links == [root, first]
    assert all("example.test" in link for link in links)


def test_quit_driver_closes_and_clears_driver():
    driver = FakeDriver({})
    scraper = ScrapeSite(driver=driver)

    scraper.quit_driver()

    assert driver.quit_called
    assert scraper.driver is None


def test_redirect_to_another_host_is_rejected_and_driver_is_closed():
    root = "https://example.test/root"
    driver = FakeDriver({root: "<p>redirected</p>"})
    driver.current_url = "https://other.test/landing"

    # Preserve the simulated redirect when the driver receives a request.
    driver.get = lambda _url: setattr(driver, "page_source", "<p>redirected</p>")
    try:
        ScrapeSite(driver=driver).get_page_links(root)
        assert False, "expected redirect boundary error"
    except ValueError:
        pass
    assert driver.quit_called


def test_relative_links_use_the_validated_final_redirect_url():
    requested = "https://example.test/start"
    final = "https://example.test/nested/index"
    driver = FakeDriver({requested: '<a href="child?ok">child</a>'})

    def redirected_get(url):
        driver.page_source = driver.pages[url]
        driver.current_url = final

    driver.get = redirected_get
    assert ScrapeSite(driver=driver).get_page_links(requested, "?ok") == [
        "https://example.test/nested/child?ok"
    ]


def test_create_experience_obj_populates_all_fields():
    soup = BeautifulSoup(f'<div class="{cfg.IDENTIFY_CONTENT}">Useful sample text</div>', "html.parser")

    experience = create_experience_obj(soup)

    assert experience.uuid
    assert experience.title
    assert experience.classification
    assert experience.description == "Useful sample text"


def test_empty_record_cannot_be_created_or_persisted(data_table):
    try:
        Experience.create(title="", classification="demo", description="text")
        assert False, "expected validation error"
    except ValueError:
        pass

    repository = DynamoExperienceRepository(table=data_table)
    try:
        repository.save(Experience(uuid="id", title="", classification="demo", description="text"))
        assert False, "expected persistence validation error"
    except ValueError:
        pass
