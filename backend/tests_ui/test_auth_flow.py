"""UI tests: landing page, signup, email verification, login, logout.

Each test checks one thing. IDs (UI-01...) match docs/test-cases.md.
"""

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from core.testing import UI_TEST_FRONTEND_URL as FRONTEND_URL
from profiles.models import Profile

from helpers import click_button, fill_signup, log_in, stored_token  # tests_ui/helpers.py

# live_server needs real commits (not a rolled-back transaction) so the
# server thread can see the data each test creates.
pytestmark = pytest.mark.django_db(transaction=True)


def field_error(wait, name):
    return wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-error-for={name}]"))
    )


def alert(wait):
    return wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[role=alert]")))


# --- Landing page ---------------------------------------------------------

def test_ui01_landing_page_sign_up_button_opens_signup(page, wait):
    page.get(f"{FRONTEND_URL}/")
    wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "h1"), "Meet students who get you."))

    page.find_element(By.XPATH, "//header//a[normalize-space()='Sign up']").click()

    wait.until(EC.url_matches(r"/signup$"))


# --- Signup + verification ------------------------------------------------

def test_ui02_signup_rejects_non_edu_email(page, wait):
    page.get(f"{FRONTEND_URL}/signup")

    fill_signup(page, "sahil@gmail.com")

    assert field_error(wait, "schoolEmail").text == "Please use your .edu school email."


def test_ui03_signup_rejects_duplicate_email(page, wait, make_user):
    make_user(school_email="sahil@tamut.edu")
    page.get(f"{FRONTEND_URL}/signup")

    fill_signup(page, "SAHIL@tamut.edu")  # same address, different case

    assert field_error(wait, "schoolEmail").text == "An account with this email already exists."


def test_ui04_signup_with_edu_email_asks_to_check_inbox(page, wait, mailoutbox):
    page.get(f"{FRONTEND_URL}/signup")

    fill_signup(page, "sahil@tamut.edu")

    wait.until(EC.url_contains("/check-email"))
    assert "sahil@tamut.edu" in page.page_source
    assert mailoutbox[0].to == ["sahil@tamut.edu"]  # the verification email went out


def test_ui05_verification_link_activates_account(page, wait, make_user):
    user = make_user(school_email="sahil@tamut.edu", is_active=False)
    # The same link the verification email contains (see users/emails.py).
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    page.get(f"{FRONTEND_URL}/verify/{uid}/{token}")

    wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "h1"), "verified"))
    user.refresh_from_db()
    assert user.is_active and user.is_edu_verified


# --- Login / logout -------------------------------------------------------

def test_ui06_login_with_wrong_password_shows_error(page, wait, make_user):
    make_user(school_email="alice@tamut.edu")

    log_in(page, "alice@tamut.edu", password="wrong-Pass-99")

    assert alert(wait).text == "Invalid email or password."


def test_ui07_unverified_user_cannot_log_in(page, wait, make_user):
    make_user(school_email="alice@tamut.edu", is_active=False)

    log_in(page, "alice@tamut.edu")

    assert alert(wait).text.startswith("Please verify your email before logging in.")


def test_ui29_unverified_user_can_resend_verification_email(page, wait, make_user, mailoutbox):
    make_user(school_email="alice@tamut.edu", is_active=False)
    log_in(page, "alice@tamut.edu")

    wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Resend the link"))).click()
    wait.until(EC.url_contains("/check-email"))
    click_button(wait, "Resend the email")

    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid=resend-notice]")))
    assert mailoutbox[-1].to == ["alice@tamut.edu"]  # a new link went out


def test_ui08_first_login_goes_to_profile_setup(page, wait, make_student):
    make_student("alice")  # verified, but no profile yet

    log_in(page, "alice@tamut.edu")

    wait.until(EC.url_contains("/profile/setup"))


def test_ui09_successful_login_lands_on_home(page, wait, make_student):
    Profile.objects.create(user=make_student("alice"), bio="Hi!")

    log_in(page, "alice@tamut.edu")

    wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "h1"), "Hey, alice"))
    assert stored_token(page)


def test_ui10_logged_out_visitor_is_redirected_to_login(page, wait):
    page.get(f"{FRONTEND_URL}/home")

    wait.until(EC.url_contains("/login"))


def test_ui11_logout_clears_session(page, wait, make_student):
    Profile.objects.create(user=make_student("alice"), bio="Hi!")
    log_in(page, "alice@tamut.edu")
    wait.until(EC.url_contains("/home"))

    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Log out']"))).click()

    wait.until(EC.url_contains("/login"))
    assert stored_token(page) is None
