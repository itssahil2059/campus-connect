import pytest
from django.core.cache import cache

from chat.models import Conversation
from connections.models import Connection


@pytest.fixture(autouse=True)
def clear_throttle_counts():
    """Rate-limit counters live in the cache; start every test fresh."""
    cache.clear()


@pytest.fixture
def connect():
    def _connect(a, b):
        return Connection.objects.create(
            from_user=a, to_user=b, status=Connection.Status.ACCEPTED
        )

    return _connect


@pytest.fixture
def alice(make_student):
    return make_student("alice")


@pytest.fixture
def bob(make_student):
    return make_student("bob")


@pytest.fixture
def carol(make_student):
    return make_student("carol")


@pytest.fixture
def chat_ab(alice, bob, connect):
    """Alice and Bob are connected and have a conversation."""
    connect(alice, bob)
    conversation, _ = Conversation.get_or_create_between(alice, bob)
    return conversation
