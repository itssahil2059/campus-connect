import pytest
from django.urls import reverse

from connections.models import Connection

LIST_URL = reverse("connections:connection-list")


def url(name, connection):
    return reverse(f"connections:connection-{name}", kwargs={"pk": connection.pk})


def with_url(user):
    return reverse("connections:connection-with-user", kwargs={"user_id": user.pk})


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
def request_ab(alice, bob):
    """A pending request from alice to bob."""
    return Connection.objects.create(from_user=alice, to_user=bob)


@pytest.mark.django_db
class TestSendRequest:
    def test_requires_login(self, api_client):
        assert api_client.get(LIST_URL).status_code == 401

    def test_send_creates_pending(self, client_for, alice, bob):
        response = client_for(alice).post(LIST_URL, {"user_id": bob.id}, format="json")

        assert response.status_code == 201
        assert response.data["status"] == "outgoing"
        assert response.data["user"]["username"] == "bob"
        assert "school_email" not in response.data["user"]
        assert Connection.objects.get().status == Connection.Status.PENDING

    def test_sending_twice_is_harmless(self, client_for, alice, bob, request_ab):
        response = client_for(alice).post(LIST_URL, {"user_id": bob.id}, format="json")

        assert response.status_code == 200
        assert Connection.objects.count() == 1

    def test_asking_back_accepts(self, client_for, alice, bob, request_ab):
        response = client_for(bob).post(LIST_URL, {"user_id": alice.id}, format="json")

        assert response.status_code == 200
        assert response.data["status"] == "connected"
        request_ab.refresh_from_db()
        assert request_ab.status == Connection.Status.ACCEPTED

    def test_cannot_request_self(self, client_for, alice):
        response = client_for(alice).post(LIST_URL, {"user_id": alice.id}, format="json")
        assert response.status_code == 400

    def test_cannot_request_unverified_or_missing_user(self, client_for, alice, make_user):
        unverified = make_user(username="dave", school_email="dave@tamut.edu")
        client = client_for(alice)

        assert client.post(LIST_URL, {"user_id": unverified.id}, format="json").status_code == 400
        assert client.post(LIST_URL, {"user_id": 99999}, format="json").status_code == 400


@pytest.mark.django_db
class TestRespond:
    def test_accept(self, client_for, bob, request_ab):
        response = client_for(bob).post(url("accept", request_ab))

        assert response.status_code == 200
        assert response.data["status"] == "connected"
        request_ab.refresh_from_db()
        assert request_ab.responded_at is not None

    def test_sender_cannot_accept_own_request(self, client_for, alice, request_ab):
        assert client_for(alice).post(url("accept", request_ab)).status_code == 400

    def test_outsider_gets_404(self, client_for, carol, request_ab):
        client = client_for(carol)
        assert client.post(url("accept", request_ab)).status_code == 404
        assert client.delete(url("detail", request_ab)).status_code == 404

    def test_decline_is_hidden_from_sender(self, client_for, alice, bob, request_ab):
        assert client_for(bob).post(url("decline", request_ab)).status_code == 204

        # Bob no longer sees it at all.
        assert client_for(bob).get(LIST_URL).data == []
        # Alice still sees an outgoing request, not a rejection.
        alice_view = client_for(alice).get(LIST_URL).data
        assert [c["status"] for c in alice_view] == ["outgoing"]

    def test_declined_sender_cannot_resend(self, client_for, alice, bob, request_ab):
        client_for(bob).post(url("decline", request_ab))

        response = client_for(alice).post(LIST_URL, {"user_id": bob.id}, format="json")

        assert response.status_code == 200
        request_ab.refresh_from_db()
        assert request_ab.status == Connection.Status.DECLINED

    def test_decliner_can_change_their_mind(self, client_for, alice, bob, request_ab):
        client_for(bob).post(url("decline", request_ab))

        response = client_for(bob).post(LIST_URL, {"user_id": alice.id}, format="json")

        assert response.status_code == 201
        assert response.data["status"] == "outgoing"
        request_ab.refresh_from_db()
        assert (request_ab.from_user, request_ab.status) == (bob, Connection.Status.PENDING)


@pytest.mark.django_db
class TestListAndRemove:
    def test_list_filters(self, client_for, alice, bob, carol, request_ab):
        Connection.objects.create(
            from_user=carol, to_user=alice, status=Connection.Status.ACCEPTED
        )
        client = client_for(alice)

        def names(status):
            data = client.get(LIST_URL, {"status": status}).data
            return [c["user"]["username"] for c in data]

        assert names("connected") == ["carol"]
        assert names("outgoing") == ["bob"]
        assert names("incoming") == []
        assert len(client.get(LIST_URL).data) == 2

    def test_connections_are_private(self, client_for, carol, request_ab):
        assert client_for(carol).get(LIST_URL).data == []

    def test_sender_can_cancel(self, client_for, alice, request_ab):
        assert client_for(alice).delete(url("detail", request_ab)).status_code == 204
        assert not Connection.objects.exists()

    def test_recipient_must_decline_not_delete(self, client_for, bob, request_ab):
        assert client_for(bob).delete(url("detail", request_ab)).status_code == 400

    def test_either_side_can_remove_connection(self, client_for, bob, request_ab):
        request_ab.status = Connection.Status.ACCEPTED
        request_ab.save()

        assert client_for(bob).delete(url("detail", request_ab)).status_code == 204
        assert not Connection.objects.exists()


@pytest.mark.django_db
class TestWithUser:
    def test_none(self, client_for, alice, bob):
        assert client_for(alice).get(with_url(bob)).data == {"status": "none", "connection": None}

    def test_each_side(self, client_for, alice, bob, request_ab):
        assert client_for(alice).get(with_url(bob)).data["status"] == "outgoing"
        assert client_for(bob).get(with_url(alice)).data["status"] == "incoming"

    def test_self_is_none(self, client_for, alice, request_ab):
        assert client_for(alice).get(with_url(alice)).data["status"] == "none"
