import pytest
from django.urls import reverse

from conftest import PASSWORD
from users.models import CustomUser

SIGNUP_URL = reverse("users:signup")


def signup_data(**overrides):
    data = {
        "username": "sahil",
        "school_email": "sahil@tamut.edu",
        "password": PASSWORD,
        "password_confirm": PASSWORD,
        "college_name": "TAMUT",
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
class TestSignup:
    def test_creates_inactive_unverified_user(self, api_client):
        response = api_client.post(SIGNUP_URL, signup_data(), format="json")

        assert response.status_code == 201
        user = CustomUser.objects.get(username="sahil")
        assert user.is_active is False
        assert user.is_edu_verified is False
        # Stored hashed, never as plain text.
        assert user.password != PASSWORD
        assert user.check_password(PASSWORD)

    def test_response_has_no_password_fields(self, api_client):
        response = api_client.post(SIGNUP_URL, signup_data(), format="json")

        assert "password" not in response.data
        assert "password_confirm" not in response.data
        assert response.data["school_email"] == "sahil@tamut.edu"

    def test_email_is_stored_lowercase(self, api_client):
        api_client.post(
            SIGNUP_URL, signup_data(school_email="Sahil@TAMUT.EDU"), format="json"
        )

        assert CustomUser.objects.get(username="sahil").school_email == "sahil@tamut.edu"

    def test_sends_verification_email(self, api_client, mailoutbox):
        # mailoutbox (from pytest-django) collects emails instead of printing them.
        api_client.post(SIGNUP_URL, signup_data(), format="json")

        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == ["sahil@tamut.edu"]
        assert "/api/auth/verify/" in mailoutbox[0].body

    @pytest.mark.parametrize(
        "email",
        ["sahil@gmail.com", "sahil@tamut.edu.com", "sahil@tamut.org"],
    )
    def test_rejects_non_edu_email(self, api_client, email, mailoutbox):
        response = api_client.post(
            SIGNUP_URL, signup_data(school_email=email), format="json"
        )

        assert response.status_code == 400
        assert response.data["school_email"] == ["Please use your .edu school email."]
        assert not CustomUser.objects.exists()
        assert mailoutbox == []

    @pytest.mark.parametrize("email", ["alice@tamut.edu", "ALICE@Tamut.EDU"])
    def test_rejects_duplicate_email_any_case(self, api_client, make_user, email):
        make_user(username="alice", school_email="alice@tamut.edu")

        response = api_client.post(
            SIGNUP_URL, signup_data(school_email=email), format="json"
        )

        assert response.status_code == 400
        assert response.data["school_email"] == [
            "An account with this email already exists."
        ]

    def test_rejects_mismatched_passwords(self, api_client):
        response = api_client.post(
            SIGNUP_URL, signup_data(password_confirm="different-Pass-99"), format="json"
        )

        assert response.status_code == 400
        assert response.data["password_confirm"] == ["Passwords do not match."]

    def test_rejects_password_similar_to_school_email(self, api_client):
        # Checks the school_email entry in AUTH_PASSWORD_VALIDATORS.
        response = api_client.post(
            SIGNUP_URL,
            signup_data(
                school_email="sahilbhusal@tamut.edu",
                password="sahilbhusal1!",
                password_confirm="sahilbhusal1!",
            ),
            format="json",
        )

        assert response.status_code == 400
        assert response.data["password"] == [
            "The password is too similar to the school email."
        ]

    def test_password_error_is_not_duplicated(self, api_client):
        # Regression: the similarity validator used to be listed twice.
        response = api_client.post(
            SIGNUP_URL,
            signup_data(password="Sahil5xyz", password_confirm="Sahil5xyz", username="sahil5"),
            format="json",
        )

        assert response.status_code == 400
        assert response.data["password"] == [
            "The password is too similar to the username."
        ]

    def test_rejects_short_common_password(self, api_client):
        response = api_client.post(
            SIGNUP_URL,
            signup_data(password="password", password_confirm="password"),
            format="json",
        )

        assert response.status_code == 400
        assert "This password is too common." in response.data["password"]

    def test_requires_college_name(self, api_client):
        response = api_client.post(
            SIGNUP_URL, signup_data(college_name=""), format="json"
        )

        assert response.status_code == 400
        assert "college_name" in response.data
