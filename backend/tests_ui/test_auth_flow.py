"""Browser tests for signup and login, clicking through the real React pages."""

import re

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from core.testing import PASSWORD
from core.testing import UI_TEST_FRONTEND_URL as FRONTEND_URL

# live_server needs real commits (not a rolled-back transaction) so the
# server thread can see the data each test creates.
pytestmark = pytest.mark.django_db(transaction=True)


def fill(browser, name, value):
    field = browser.find_element(By.NAME, name)
    field.clear()
    field.send_keys(value)


def submit(browser):
    browser.find_element(By.CSS_SELECTOR, "button[type=submit]").click()


def fill_signup(browser, email):
    fill(browser, "username", "sahil")
    fill(browser, "schoolEmail", email)
    fill(browser, "collegeName", "TAMUT")
    fill(browser, "password", PASSWORD)
    fill(browser, "passwordConfirm", PASSWORD)
    submit(browser)


def log_in(browser, email, password=PASSWORD):
    browser.get(f"{FRONTEND_URL}/login")
    fill(browser, "schoolEmail", email)
    fill(browser, "password", password)
    submit(browser)


class TestSignup:
    def test_rejects_non_edu_email(self, page, wait):
        page.get(f"{FRONTEND_URL}/signup")

        fill_signup(page, "sahil@gmail.com")

        error = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-error-for=schoolEmail]"))
        )
        assert error.text == "Please use your .edu school email."
        assert page.current_url.endswith("/signup")

    def test_rejects_duplicate_email(self, page, wait, make_user):
        make_user(school_email="sahil@tamut.edu")
        page.get(f"{FRONTEND_URL}/signup")

        fill_signup(page, "SAHIL@tamut.edu")

        error = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-error-for=schoolEmail]"))
        )
        assert error.text == "An account with this email already exists."

    def test_signup_verify_then_login(self, page, wait, mailoutbox):
        """The full happy path: signup -> email link -> verified -> login -> profile setup."""
        page.get(f"{FRONTEND_URL}/signup")
        fill_signup(page, "sahil@tamut.edu")

        wait.until(EC.url_contains("/check-email"))
        assert "sahil@tamut.edu" in page.page_source

        # Open the link from the captured verification email, like the user would.
        link = re.search(r"http://\S+/verify/\S+", mailoutbox[0].body).group()
        page.get(link)
        wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "h1"), "verified"))

        log_in(page, "sahil@tamut.edu")

        # First login with no profile yet -> profile setup.
        wait.until(EC.url_contains("/profile/setup"))
        assert page.execute_script("return localStorage.getItem('token')")


class TestLogin:
    def test_wrong_password_shows_error(self, page, wait, make_user):
        make_user(school_email="alice@tamut.edu")

        log_in(page, "alice@tamut.edu", password="wrong-Pass-99")

        alert = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[role=alert]")))
        assert alert.text == "Invalid email or password."
        assert page.current_url.endswith("/login")

    def test_unverified_user_cannot_log_in(self, page, wait, make_user):
        make_user(school_email="alice@tamut.edu", is_active=False)

        log_in(page, "alice@tamut.edu")

        alert = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[role=alert]")))
        assert alert.text == "Please verify your email before logging in."

    def test_verified_user_lands_on_home_and_can_log_out(self, page, wait, make_user):
        from profiles.models import Profile

        alice = make_user(school_email="alice@tamut.edu", is_edu_verified=True)
        Profile.objects.create(user=alice, bio="Hi!")

        log_in(page, "alice@tamut.edu")

        wait.until(EC.url_contains("/home"))
        wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "h1"), "Hey, alice"))

        page.find_element(By.XPATH, "//button[text()='Log out']").click()
        wait.until(EC.url_contains("/login"))
        assert page.execute_script("return localStorage.getItem('token')") is None

    def test_logged_out_visitor_is_sent_to_login(self, page, wait):
        page.get(f"{FRONTEND_URL}/home")

        wait.until(EC.url_contains("/login"))
