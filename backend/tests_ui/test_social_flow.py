"""Browser tests for connections and chat, clicking through the real React pages.

pytest-django's live_server is a plain (WSGI) server without WebSocket
support, so the chat page can't go live here and falls back to polling.
That makes these tests a check of the fallback path too. The WebSocket
itself is covered by chat/tests/test_consumers.py.
"""

import pytest
from rest_framework.authtoken.models import Token
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

from chat.models import Conversation
from chat.services import send_message
from connections.models import Connection
from core.testing import UI_TEST_FRONTEND_URL as FRONTEND_URL
from profiles.models import Profile

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def alice(make_student):
    user = make_student("alice")
    Profile.objects.create(user=user, bio="Alice's bio")
    return user


@pytest.fixture
def bob(make_student):
    user = make_student("bob")
    Profile.objects.create(user=user, bio="Bob's bio")
    return user


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


def test_connect_accept_then_message(page, wait, alice, bob):
    # Alice finds Bob's profile and sends a request.
    log_in_as(page, alice, f"/profile/{bob.profile.id}")
    click_button(wait, "Connect")
    wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "[data-testid=connect-controls]"), "Requested"))
    assert Connection.objects.get().status == Connection.Status.PENDING

    # Bob sees it waiting under Requests and accepts.
    log_in_as(page, bob, "/friends")
    row = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid=incoming-row]")))
    assert "alice" in row.text
    click_button(wait, "Accept")
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid=incoming-row]")))
    assert Connection.objects.get().status == Connection.Status.ACCEPTED

    # Alice now appears under Connections; Message opens the chat.
    page.find_element(By.XPATH, "//button[starts-with(normalize-space(), 'Connections')]").click()
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid=connection-row]")))
    click_button(wait, "Message")
    wait.until(EC.url_matches(r"/messages/\d+$"))
    assert Conversation.objects.count() == 1


def test_chat_send_and_receive(page, wait, alice, bob):
    Connection.objects.create(from_user=alice, to_user=bob, status=Connection.Status.ACCEPTED)
    chat, _ = Conversation.get_or_create_between(alice, bob)
    send_message(chat, bob, "hey alice!")

    # The chat list shows Bob's message as unread.
    log_in_as(page, alice, "/messages")
    row = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid=conversation-row]")))
    assert "hey alice!" in row.text
    assert row.find_element(By.CSS_SELECTOR, "[data-testid=unread-badge]").text == "1"

    # Open it: Bob's message is there, and opening marks it read.
    row.click()
    wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "[data-testid=message-list]"), "hey alice!"))
    wait.until(lambda _: chat.messages.filter(read_at__isnull=False).exists())

    # Alice replies with Enter.
    box = page.find_element(By.NAME, "message")
    box.send_keys("hi bob", Keys.ENTER)
    wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "[data-testid=message-list]"), "hi bob"))
    assert chat.messages.filter(sender=alice, body="hi bob").exists()
    assert box.get_attribute("value") == ""

    # Bob replies (from "another device"); it shows up without a reload.
    send_message(chat, bob, "how's it going?")
    wait.until(
        EC.text_to_be_present_in_element((By.CSS_SELECTOR, "[data-testid=message-list]"), "how's it going?")
    )


def test_chat_after_disconnect_is_read_only(page, wait, alice, bob):
    chat, _ = Conversation.get_or_create_between(alice, bob)  # never/no longer connected

    log_in_as(page, alice, f"/messages/{chat.id}")

    wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "form"), "no longer connected"))
    assert not page.find_elements(By.NAME, "message")


def test_discover_add_friend_then_message(page, wait, alice, bob):
    # Alice finds Bob under Discover > Everyone and adds him.
    log_in_as(page, alice, "/discover")
    click_button(wait, "Everyone")
    click_button(wait, "Add friend")
    wait.until(EC.visibility_of_element_located((By.XPATH, "//button[normalize-space()='Request sent']")))
    connection = Connection.objects.get()
    assert (connection.from_user, connection.to_user) == (alice, bob)

    # Bob accepts (his side is covered above). After a reload, Bob is still
    # under Alice's Friends tab, so friends come from the server, not memory.
    connection.status = Connection.Status.ACCEPTED
    connection.save()
    page.refresh()
    click_button(wait, "Friends")
    card = wait.until(EC.visibility_of_element_located((By.XPATH, "//article[contains(., 'bob')]")))

    # Message opens a real chat with Bob.
    card.find_element(By.XPATH, ".//button[normalize-space()='Message']").click()
    wait.until(EC.url_matches(r"/messages/\d+$"))
    chat = Conversation.objects.get()
    assert page.current_url.endswith(f"/messages/{chat.id}")
