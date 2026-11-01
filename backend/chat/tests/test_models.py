import pytest
from django.db import IntegrityError

from chat.models import Conversation, Message
from chat.services import NotAllowed, mark_read, send_message
from connections.models import Connection


@pytest.mark.django_db
class TestConversation:
    def test_same_row_whichever_side_opens_it(self, alice, bob):
        first, created = Conversation.get_or_create_between(bob, alice)
        second, created_again = Conversation.get_or_create_between(alice, bob)

        assert created and not created_again
        assert first == second
        assert first.user_a_id < first.user_b_id

    def test_db_rejects_unordered_pair(self, alice, bob):
        low, high = sorted([alice, bob], key=lambda u: u.id)
        with pytest.raises(IntegrityError):
            Conversation.objects.create(user_a=high, user_b=low)

    def test_other_user_and_participants(self, chat_ab, alice, bob, carol):
        assert chat_ab.other_user(alice) == bob
        assert chat_ab.other_user(bob) == alice
        assert chat_ab.has_participant(alice)
        assert not chat_ab.has_participant(carol)


@pytest.mark.django_db
class TestServices:
    def test_send_saves_and_bumps_conversation(self, chat_ab, alice):
        before = chat_ab.updated_at

        message = send_message(chat_ab, alice, "hi")

        chat_ab.refresh_from_db()
        assert Message.objects.get() == message
        assert chat_ab.updated_at >= before
        assert chat_ab.updated_at == message.created_at

    def test_outsider_cannot_send(self, chat_ab, carol):
        with pytest.raises(NotAllowed):
            send_message(chat_ab, carol, "hi")

    def test_cannot_send_after_disconnect(self, chat_ab, alice):
        Connection.objects.all().delete()
        with pytest.raises(NotAllowed):
            send_message(chat_ab, alice, "hi")

    def test_mark_read_only_marks_the_other_persons_messages(self, chat_ab, alice, bob):
        mine = send_message(chat_ab, alice, "from alice")
        theirs = send_message(chat_ab, bob, "from bob")

        assert mark_read(chat_ab, alice) == 1

        mine.refresh_from_db()
        theirs.refresh_from_db()
        assert mine.read_at is None
        assert theirs.read_at is not None

    def test_str(self, chat_ab, alice):
        assert str(send_message(chat_ab, alice, "hello there")) == "alice: hello there"
