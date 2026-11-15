"""Small helpers shared by the UI tests (fixtures live in conftest.py)."""

from rest_framework.authtoken.models import Token
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from core.testing import UI_TEST_FRONTEND_URL as FRONTEND_URL


def log_in_as(browser, user, path):
    """Skip the login form (covered in test_auth_flow): store the token, open the page."""
    token, _ = Token.objects.get_or_create(user=user)
    browser.get(FRONTEND_URL)
    browser.execute_script("localStorage.setItem('token', arguments[0])", token.key)
    browser.get(f"{FRONTEND_URL}{path}")


def click_button(wait, text):
    wait.until(
        EC.element_to_be_clickable((By.XPATH, f"//button[normalize-space()='{text}']"))
    ).click()
