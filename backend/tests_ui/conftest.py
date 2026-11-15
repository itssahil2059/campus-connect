"""Fixtures for browser (Selenium) tests.

Each run starts:
  - a throwaway Django server on the test database (pytest-django's live_server)
  - a Vite dev server for the React app, pointed at that Django server
  - headless Chrome (set HEADED=1 to watch the browser)

Run with:  cd backend && pytest tests_ui
"""

import os
import signal
import socket
import subprocess
import time
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from core.testing import UI_TEST_FRONTEND_PORT as FRONTEND_PORT
from core.testing import UI_TEST_FRONTEND_URL as FRONTEND_URL

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


def _wait_for_port(port, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        # create_connection tries IPv4 and IPv6 (Vite may listen on ::1).
        try:
            socket.create_connection(("localhost", port), timeout=1).close()
            return
        except OSError:
            time.sleep(0.3)
    raise RuntimeError(f"Frontend didn't start on port {port}")


@pytest.fixture(scope="session")
def frontend(live_server):
    """Start Vite with VITE_API_URL pointing at the test Django server."""
    if not (FRONTEND_DIR / "node_modules").exists():
        pytest.skip("Run `npm install` in frontend/ first.")

    proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", str(FRONTEND_PORT), "--strictPort"],
        cwd=FRONTEND_DIR,
        env={**os.environ, "VITE_API_URL": live_server.url},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,  # own process group, so we can stop npm + vite together
    )
    try:
        _wait_for_port(FRONTEND_PORT)
        yield FRONTEND_URL
    finally:
        os.killpg(proc.pid, signal.SIGTERM)


@pytest.fixture(autouse=True)
def _frontend_settings(settings):
    # Let the test frontend call the API, and put its URL in emailed links.
    settings.CORS_ALLOWED_ORIGINS = [FRONTEND_URL]
    settings.FRONTEND_URL = FRONTEND_URL


@pytest.fixture(scope="session")
def browser():
    options = webdriver.ChromeOptions()
    if not os.environ.get("HEADED"):
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")
    driver = webdriver.Chrome(options=options)  # Selenium finds/downloads chromedriver
    yield driver
    driver.quit()


@pytest.fixture
def page(browser, frontend):
    """The browser, starting each test logged out on a blank page."""
    browser.get(frontend)
    browser.execute_script("localStorage.clear()")
    return browser


@pytest.fixture
def wait(browser):
    return WebDriverWait(browser, 10)


@pytest.fixture
def alice(make_student):
    from profiles.models import Profile

    user = make_student("alice")
    Profile.objects.create(user=user, bio="Alice's bio")
    return user


@pytest.fixture
def bob(make_student):
    from profiles.models import Profile

    user = make_student("bob")
    Profile.objects.create(user=user, bio="Bob's bio")
    return user
