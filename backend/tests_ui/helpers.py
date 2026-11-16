"""Small helpers shared by the UI tests (fixtures live in conftest.py)."""

from rest_framework.authtoken.models import Token
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from core.testing import PASSWORD
from core.testing import UI_TEST_FRONTEND_URL as FRONTEND_URL


def fill(browser, name, value):
    """Type into the form field with this name="..." (clearing it first)."""
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
    """Log in through the real login form."""
    browser.get(f"{FRONTEND_URL}/login")
    fill(browser, "schoolEmail", email)
    fill(browser, "password", password)
    submit(browser)


def log_in_as(browser, user, path):
    """Skip the login form (tested on its own): store the token, open the page."""
    token, _ = Token.objects.get_or_create(user=user)
    browser.get(FRONTEND_URL)
    browser.execute_script("localStorage.setItem('token', arguments[0])", token.key)
    browser.get(f"{FRONTEND_URL}{path}")


def click_button(wait, text):
    """Wait until a <button> with exactly this text can be clicked, then click it."""
    wait.until(
        EC.element_to_be_clickable((By.XPATH, f"//button[normalize-space()='{text}']"))
    ).click()


def stored_token(browser):
    return browser.execute_script("return localStorage.getItem('token')")


def set_date(browser, name, iso_date):
    """Fill an <input type=date> with "YYYY-MM-DD".

    Typing into Chrome's date picker depends on the computer's locale
    (mm/dd/yyyy vs dd/mm/yyyy), so set the value the way React expects:
    through the native value setter, then fire an "input" event.
    """
    field = browser.find_element(By.NAME, name)
    browser.execute_script(
        """
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
        setter.call(arguments[0], arguments[1]);
        arguments[0].dispatchEvent(new Event("input", { bubbles: true }));
        """,
        field,
        iso_date,
    )
