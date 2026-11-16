"""UI tests: profile setup + questionnaire, feed, links, search.

Each test checks one thing. IDs (UI-12...) match docs/test-cases.md.
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

from profiles.models import Answer, Profile, Question

from helpers import click_button, log_in_as  # tests_ui/helpers.py

pytestmark = pytest.mark.django_db(transaction=True)


def test_ui12_questionnaire_answers_are_saved(page, wait, make_student):
    alice = make_student("alice")  # no profile yet -> setup page
    question = Question.objects.create(
        text="Are you a morning person?", choices=["Early bird", "Night owl"], order=0
    )
    log_in_as(page, alice, "/profile/setup")

    wait.until(EC.element_to_be_clickable((
        By.XPATH, "//fieldset[contains(., 'Are you a morning person?')]//button[normalize-space()='Night owl']"
    ))).click()
    click_button(wait, "Finish setup")

    wait.until(EC.url_contains("/home"))
    assert Answer.objects.get(user=alice, question=question).choice == "Night owl"


def test_ui13_feed_lists_other_students_not_yourself(page, wait, alice, bob):
    log_in_as(page, alice, "/home")

    cards = wait.until(
        EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "[data-testid=profile-card]"))
    )

    assert [c.find_element(By.CSS_SELECTOR, "p.font-semibold").text for c in cards] == ["bob"]


def test_ui14_profile_link_shows_on_profile_page(page, wait, alice, bob):
    # Alice adds her GitHub on the edit page (no https://, like most people type it).
    log_in_as(page, alice, "/profile/edit")
    wait.until(EC.visibility_of_element_located((By.NAME, "link-0"))).send_keys("github.com/alice")
    click_button(wait, "Save changes")
    wait.until(EC.url_contains("/home"))

    # Bob sees it as a link that opens in a new tab.
    log_in_as(page, bob, f"/profile/{alice.profile.id}")
    link = wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "github.com/alice")))
    assert link.get_attribute("href") == "https://github.com/alice"


def search_results(page):
    """Usernames on the result cards, or None while the count and cards disagree."""
    count = page.find_element(By.CSS_SELECTOR, "[data-testid=search-count]").text
    cards = page.find_elements(By.XPATH, "//article//p[contains(@class, 'font-semibold')]")
    return sorted(c.text for c in cards) if count.startswith(str(len(cards))) else None


@pytest.fixture
def search_page(page, wait, alice, bob, make_student):
    """Discover > Search as Alice, with Bob (likes coffee) and Carol (night owl)."""
    Profile.objects.filter(user=bob).update(interests=["hiking"], likes=["coffee"])
    Profile.objects.create(user=make_student("carol"), bio="Night owl", interests=["hiking"])
    log_in_as(page, alice, "/discover")
    click_button(wait, "Search")
    wait.until(lambda _: search_results(page) == ["bob", "carol"])
    return page


def test_ui15_search_filters_by_like_tag(search_page, wait):
    search_page.find_element(By.NAME, "search-like").send_keys("coffee", Keys.ENTER)

    wait.until(lambda _: search_results(search_page) == ["bob"])


def test_ui16_search_matches_bio_text(search_page, wait):
    search_page.find_element(By.ID, "discover-search").send_keys("night owl")

    wait.until(lambda _: search_results(search_page) == ["carol"])
