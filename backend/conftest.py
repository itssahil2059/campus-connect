import pytest
from rest_framework.test import APIClient

from core.testing import PASSWORD
from users.models import CustomUser


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
