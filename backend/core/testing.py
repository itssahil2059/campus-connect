"""Shared constants for the test suites (unit and UI)."""

# Passes all of Django's password validators.
PASSWORD = "blue-Otter-42!"

# Port/URL for the React dev server started by the UI tests (tests_ui/).
# Not 5173, so it doesn't clash with your normal dev server.
UI_TEST_FRONTEND_PORT = 5174
UI_TEST_FRONTEND_URL = f"http://localhost:{UI_TEST_FRONTEND_PORT}"
