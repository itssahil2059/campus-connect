"""UI tests: friend requests, chat, Discover connect/remove.

pytest-django's live_server is a plain (WSGI) server without WebSocket
support, so the chat page can't go live here and falls back to polling.
That makes these tests a check of the fallback path too. The WebSocket
itself is covered by chat/tests/test_consumers.py.

Each test checks one thing. IDs (UI-17...) match docs/test-cases.md.
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

from chat.models import Conversation
from chat.services import send_message
from connections.models import Connection

from helpers import click_button, log_in_as, open_discover  # tests_ui/helpers.py

pytestmark = pytest.mark.django_db(transaction=True)

CONNECT_CONTROLS = (By.CSS_SELECTOR, "[data-testid=connect-controls]")
MESSAGE_LIST = (By.CSS_SELECTOR, "[data-testid=message-list]")


@pytest.fixture
def friends(alice, bob):
    """Alice and Bob are connected."""
    Connection.objects.create(from_user=alice, to_user=bob, status=Connection.Status.ACCEPTED)


@pytest.fixture
def chat(alice, bob, friends):
    conversation, _ = Conversation.get_or_create_between(alice, bob)
    return conversation


# --- Friend requests ------------------------------------------------------

def test_ui17_connect_sends_friend_request(page, wait, alice, bob):
    log_in_as(page, alice, f"/profile/{bob.profile.id}")

    click_button(wait, "Connect")

    wait.until(EC.text_to_be_present_in_element(CONNECT_CONTROLS, "Requested"))
    assert Connection.objects.get().status == Connection.Status.PENDING


def test_ui18_accepting_request_connects_both_students(page, wait, alice, bob):
    Connection.objects.create(from_user=alice, to_user=bob)  # pending
    log_in_as(page, bob, "/friends")
    row = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid=incoming-row]")))
    assert "alice" in row.text

    click_button(wait, "Accept")

    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid=incoming-row]")))
    assert Connection.objects.get().status == Connection.Status.ACCEPTED


def test_ui19_message_button_opens_chat_with_friend(page, wait, alice, friends):
    log_in_as(page, alice, "/friends")
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[starts-with(normalize-space(), 'Connections')]")
    )).click()
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid=connection-row]")))

    click_button(wait, "Message")

    wait.until(EC.url_matches(r"/messages/\d+$"))
    assert page.current_url.endswith(f"/messages/{Conversation.objects.get().id}")


# --- Chat -----------------------------------------------------------------

def test_ui20_sending_a_message_shows_it_in_chat(page, wait, alice, chat):
    log_in_as(page, alice, f"/messages/{chat.id}")

    wait.until(EC.visibility_of_element_located((By.NAME, "message"))).send_keys("hi bob", Keys.ENTER)

    wait.until(EC.text_to_be_present_in_element(MESSAGE_LIST, "hi bob"))
    assert chat.messages.filter(sender=alice, body="hi bob").exists()


def test_ui21_unread_message_shows_badge_in_chat_list(page, wait, alice, bob, chat):
    send_message(chat, bob, "hey alice!")

    log_in_as(page, alice, "/messages")

    row = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid=conversation-row]")))
    assert "hey alice!" in row.text
    assert row.find_element(By.CSS_SELECTOR, "[data-testid=unread-badge]").text == "1"


def test_ui22_new_message_appears_without_reload(page, wait, alice, bob, chat):
    log_in_as(page, alice, f"/messages/{chat.id}")
    wait.until(EC.visibility_of_element_located(MESSAGE_LIST))

    send_message(chat, bob, "how's it going?")  # Bob replies from "another device"

    wait.until(EC.text_to_be_present_in_element(MESSAGE_LIST, "how's it going?"))


def test_ui23_chat_after_disconnect_is_read_only(page, wait, alice, bob):
    chat, _ = Conversation.get_or_create_between(alice, bob)  # never/no longer connected

    log_in_as(page, alice, f"/messages/{chat.id}")

    wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "form"), "no longer connected"))
    assert not page.find_elements(By.NAME, "message")


# --- Discover -------------------------------------------------------------

def test_ui24_discover_connect_sends_friend_request(page, wait, alice, bob):
    open_discover(page, wait, alice)
    click_button(wait, "Everyone")

    click_button(wait, "Connect")

    wait.until(EC.text_to_be_present_in_element(CONNECT_CONTROLS, "Requested"))
    connection = Connection.objects.get()
    assert (connection.from_user, connection.to_user) == (alice, bob)


def test_ui25_discover_remove_takes_friend_off_friends_tab(page, wait, alice, friends):
    open_discover(page, wait, alice)
    click_button(wait, "Friends")
    wait.until(EC.visibility_of_element_located((By.XPATH, "//article[contains(., 'bob')]")))

    click_button(wait, "Remove")
    page.switch_to.alert.accept()  # "Remove this connection?"

    wait.until(EC.invisibility_of_element_located((By.XPATH, "//article[contains(., 'bob')]")))
    assert not Connection.objects.exists()
