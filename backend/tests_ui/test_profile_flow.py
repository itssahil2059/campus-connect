"""Browser tests for editing a profile and finding other students."""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

from profiles.models import Profile

from helpers import click_button, log_in_as  # tests_ui/helpers.py

pytestmark = pytest.mark.django_db(transaction=True)


def test_add_link_shows_on_profile(page, wait, alice, bob):
    # Alice adds her GitHub on the edit page (no https://, like most people type it).
    log_in_as(page, alice, "/profile/edit")
    wait.until(EC.visibility_of_element_located((By.NAME, "link-0"))).send_keys("github.com/alice")
    click_button(wait, "Save changes")
    wait.until(EC.url_contains("/home"))
    assert Profile.objects.get(user=alice).links == ["https://github.com/alice"]

    # Bob sees it as a link that opens in a new tab.
    log_in_as(page, bob, f"/profile/{alice.profile.id}")
    link = wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "github.com/alice")))
    assert link.get_attribute("href") == "https://github.com/alice"
    assert link.get_attribute("target") == "_blank"


def test_search_by_text_and_tags(page, wait, alice, bob, make_student):
    Profile.objects.filter(user=bob).update(interests=["hiking"], likes=["coffee"])
    carol = make_student("carol")
    Profile.objects.create(user=carol, bio="Night owl", interests=["hiking"])

    log_in_as(page, alice, "/discover")
    click_button(wait, "Search")

    def results():
        """Usernames on the result cards, once the count matches the cards."""
        count = page.find_element(By.CSS_SELECTOR, "[data-testid=search-count]").text
        cards = page.find_elements(By.XPATH, "//article//p[contains(@class, 'font-semibold')]")
        return sorted(c.text for c in cards) if count.startswith(str(len(cards))) else None

    wait.until(lambda _: results() == ["bob", "carol"])

    # A tag filter narrows it down on the server: only Bob likes coffee.
    page.find_element(By.NAME, "search-like").send_keys("coffee", Keys.ENTER)
    wait.until(lambda _: results() == ["bob"])

    # Clear, then search text in the bio.
    click_button(wait, "Clear")
    page.find_element(By.ID, "discover-search").send_keys("night owl")
    wait.until(lambda _: results() == ["carol"])
