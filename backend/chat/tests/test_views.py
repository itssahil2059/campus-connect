import pytest
from django.urls import reverse

from chat import views
from chat.models import Conversation, Message
from chat.services import send_message
from connections.models import Connection

LIST_URL = reverse("chat:conversation-list")


def detail_url(conversation):
    return reverse("chat:conversation-detail", kwargs={"pk": conversation.pk})


def messages_url(conversation):
    return reverse("chat:conversation-messages", kwargs={"pk": conversation.pk})


def read_url(conversation):
    return reverse("chat:conversation-read", kwargs={"pk": conversation.pk})


@pytest.mark.django_db
class TestStartConversation:
    def test_requires_login(self, api_client):
        assert api_client.get(LIST_URL).status_code == 401

    def test_start_with_connection(self, client_for, alice, bob, connect):
        connect(alice, bob)

        first = client_for(alice).post(LIST_URL, {"user_id": bob.id}, format="json")
        again = client_for(bob).post(LIST_URL, {"user_id": alice.id}, format="json")

        assert first.status_code == 201
        assert again.status_code == 200
        assert first.data["id"] == again.data["id"]
        assert first.data["other_user"]["username"] == "bob"
        assert first.data["is_connected"] is True
        assert Conversation.objects.count() == 1

    def test_not_connected_is_403(self, client_for, alice, bob):
        response = client_for(alice).post(LIST_URL, {"user_id": bob.id}, format="json")
        assert response.status_code == 403
        assert not Conversation.objects.exists()

    def test_pending_request_is_not_enough(self, client_for, alice, bob):
        Connection.objects.create(from_user=alice, to_user=bob)
        response = client_for(alice).post(LIST_URL, {"user_id": bob.id}, format="json")
        assert response.status_code == 403

    def test_bad_user_id(self, client_for, alice):
        client = client_for(alice)
        assert client.post(LIST_URL, {"user_id": alice.id}, format="json").status_code == 400
        assert client.post(LIST_URL, {"user_id": 99999}, format="json").status_code == 400


@pytest.mark.django_db
class TestList:
    def test_only_my_chats_with_summary(self, client_for, chat_ab, alice, bob, carol, connect):
        send_message(chat_ab, bob, "hey alice")
        send_message(chat_ab, bob, "you there?")
        connect(bob, carol)
        Conversation.get_or_create_between(bob, carol)

        data = client_for(alice).get(LIST_URL).data

        assert len(data) == 1
        chat = data[0]
        assert chat["other_user"]["username"] == "bob"
        assert chat["last_message"]["body"] == "you there?"
        assert chat["unread_count"] == 2
        assert "school_email" not in str(chat)

    def test_latest_activity_first(self, client_for, chat_ab, alice, carol, connect):
        connect(alice, carol)
        chat_ac, _ = Conversation.get_or_create_between(alice, carol)
        send_message(chat_ab, alice, "older")
        send_message(chat_ac, alice, "newer")

        ids = [c["id"] for c in client_for(alice).get(LIST_URL).data]

        assert ids == [chat_ac.id, chat_ab.id]

    def test_disconnected_chat_still_listed(self, client_for, chat_ab, alice):
        send_message(chat_ab, alice, "hi")
        Connection.objects.all().delete()

        chat = client_for(alice).get(LIST_URL).data[0]

        assert chat["is_connected"] is False
        assert chat["last_message"]["body"] == "hi"

    def test_outsider_gets_404(self, client_for, chat_ab, carol):
        client = client_for(carol)
        assert client.get(detail_url(chat_ab)).status_code == 404
        assert client.get(messages_url(chat_ab)).status_code == 404
        assert client.post(messages_url(chat_ab), {"body": "hi"}, format="json").status_code == 404
        assert client.post(read_url(chat_ab)).status_code == 404


@pytest.mark.django_db
class TestMessages:
    def test_send_and_read_history(self, client_for, chat_ab, alice, bob):
        sent = client_for(alice).post(messages_url(chat_ab), {"body": "  hi bob  "}, format="json")

        assert sent.status_code == 201
        assert sent.data["body"] == "hi bob"
        assert sent.data["sender_id"] == alice.id
        assert sent.data["conversation_id"] == chat_ab.id

        history = client_for(bob).get(messages_url(chat_ab)).data
        assert [m["body"] for m in history["results"]] == ["hi bob"]
        assert history["has_more"] is False

    def test_blank_or_too_long_rejected(self, client_for, chat_ab, alice):
        client = client_for(alice)
        assert client.post(messages_url(chat_ab), {"body": "   "}, format="json").status_code == 400
        assert client.post(messages_url(chat_ab), {"body": "x" * 2001}, format="json").status_code == 400
        assert not Message.objects.exists()

    def test_cannot_send_after_disconnect(self, client_for, chat_ab, alice):
        Connection.objects.all().delete()
        response = client_for(alice).post(messages_url(chat_ab), {"body": "hi"}, format="json")
        assert response.status_code == 403

    def test_after_returns_only_newer(self, client_for, chat_ab, alice, bob):
        first = send_message(chat_ab, alice, "one")
        send_message(chat_ab, bob, "two")
        send_message(chat_ab, alice, "three")

        data = client_for(bob).get(messages_url(chat_ab), {"after": first.id}).data

        assert [m["body"] for m in data["results"]] == ["two", "three"]

    def test_paging_back_with_before(self, client_for, chat_ab, alice, monkeypatch):
        monkeypatch.setattr(views, "PAGE_SIZE", 2)
        for text in ["m1", "m2", "m3", "m4", "m5"]:
            send_message(chat_ab, alice, text)
        client = client_for(alice)

        latest = client.get(messages_url(chat_ab)).data
        older = client.get(messages_url(chat_ab), {"before": latest["results"][0]["id"]}).data
        oldest = client.get(messages_url(chat_ab), {"before": older["results"][0]["id"]}).data

        assert [m["body"] for m in latest["results"]] == ["m4", "m5"]
        assert [m["body"] for m in older["results"]] == ["m2", "m3"]
        assert [m["body"] for m in oldest["results"]] == ["m1"]
        assert (latest["has_more"], older["has_more"], oldest["has_more"]) == (True, True, False)

    def test_bad_cursor(self, client_for, chat_ab, alice):
        response = client_for(alice).get(messages_url(chat_ab), {"after": "abc"})
        assert response.status_code == 400

    def test_mark_read(self, client_for, chat_ab, alice, bob):
        send_message(chat_ab, bob, "hi")
        client = client_for(alice)

        assert client.post(read_url(chat_ab)).status_code == 204
        assert client.get(LIST_URL).data[0]["unread_count"] == 0
        assert Message.objects.get().read_at is not None

    def test_sending_is_rate_limited(self, client_for, chat_ab, alice, monkeypatch):
        # DRF reads the rates once at import, so patch the class, not settings.
        monkeypatch.setattr(views.SendMessageThrottle, "THROTTLE_RATES", {"chat_send": "2/min"})
        client = client_for(alice)
        codes = [
            client.post(messages_url(chat_ab), {"body": "hi"}, format="json").status_code
            for _ in range(3)
        ]
        assert codes == [201, 201, 429]
        # Reading isn't limited.
        assert client.get(messages_url(chat_ab)).status_code == 200
