import pytest
from django.db import IntegrityError

from connections.models import Connection, are_connected


@pytest.fixture
def alice(make_student):
    return make_student("alice")


@pytest.fixture
def bob(make_student):
    return make_student("bob")


@pytest.mark.django_db
class TestConnectionModel:
    def test_one_row_per_pair_in_either_direction(self, alice, bob):
        Connection.objects.create(from_user=alice, to_user=bob)

        with pytest.raises(IntegrityError):
            Connection.objects.create(from_user=bob, to_user=alice)

    def test_cannot_connect_to_self(self, alice):
        with pytest.raises(IntegrityError):
            Connection.objects.create(from_user=alice, to_user=alice)

    def test_are_connected_only_when_accepted(self, alice, bob):
        connection = Connection.objects.create(from_user=alice, to_user=bob)
        assert not are_connected(alice, bob)

        connection.status = Connection.Status.ACCEPTED
        connection.save()

        assert are_connected(alice, bob)
        assert are_connected(bob, alice)

    def test_status_for_each_side(self, alice, bob):
        connection = Connection.objects.create(from_user=alice, to_user=bob)

        assert connection.status_for(alice) == "outgoing"
        assert connection.status_for(bob) == "incoming"

        # A decline still looks pending to the sender.
        connection.status = Connection.Status.DECLINED
        assert connection.status_for(alice) == "outgoing"

    def test_str(self, alice, bob):
        connection = Connection(from_user=alice, to_user=bob)
        assert str(connection) == "alice -> bob (pending)"
