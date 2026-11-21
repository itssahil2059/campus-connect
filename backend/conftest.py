import pytest
from django.core.cache import cache
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from core.testing import PASSWORD
from users.models import CustomUser


def pytest_addoption(parser):
    # Declared here (the root conftest) because pytest only reads custom
    # options from conftest files it loads at startup. Used by tests_ui/.
    parser.addoption(
        "--headed",
        action="store_true",
        help="UI tests: show the Chrome window instead of running headless "
        "(same as HEADED=1).",
    )


@pytest.fixture(autouse=True)
def clear_throttle_counts():
    """Rate-limit counters live in the cache; start every test fresh."""
    cache.clear()


@pytest.fixture
def api_client():
    """A DRF test client: sends JSON requests to the app without a real server."""
    return APIClient()


@pytest.fixture
def make_user(db):
    """Factory for users in any state, e.g. make_user(is_active=False)."""

    def _make_user(username="alice", school_email="alice@tamut.edu", **extra):
        extra.setdefault("college_name", "TAMUT")
        return CustomUser.objects.create_user(
            username=username,
            school_email=school_email,
            password=PASSWORD,
            **extra,
        )

    return _make_user


@pytest.fixture
def client_for(db):
    """Returns an API client already logged in as the given user."""

    def _client_for(user):
        client = APIClient()
        token, _ = Token.objects.get_or_create(user=user)
        client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        return client

    return _client_for


@pytest.fixture
def make_student(make_user):
    """A verified, active student: make_student("bob")."""

    def _make_student(username, **extra):
        extra.setdefault("is_edu_verified", True)
        return make_user(
            username=username, school_email=f"{username}@tamut.edu", **extra
        )

    return _make_student


@pytest.fixture(autouse=True)
def in_memory_channel_layer(settings):
    """Chat broadcasts go to an in-process layer, so tests don't need Redis."""
    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
    }
