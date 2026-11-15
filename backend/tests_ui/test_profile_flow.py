"""Browser tests for editing a profile and finding other students."""

import pytest
from selenium.webdriver.common.by import By
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
