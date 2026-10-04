import re

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from conftest import PASSWORD
from users.models import CustomUser

SIGNUP_URL = reverse("users:signup")
LOGIN_URL = reverse("users:login")


def verify_url(uid, token):
    return reverse("users:verify", kwargs={"uidb64": uid, "token": token})


def link_parts(user):
    """The uid/token pair that would go into this user's verification email."""
    return (
        urlsafe_base64_encode(force_bytes(user.pk)),
        default_token_generator.make_token(user),
    )


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
        assert "http://localhost:5173/verify/" in mailoutbox[0].body

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


@pytest.mark.django_db
class TestEmailVerification:
    def test_full_flow_signup_email_link_verify_login(self, api_client, mailoutbox):
        signup = {
            "username": "sahil",
            "school_email": "sahil@tamut.edu",
            "password": PASSWORD,
            "password_confirm": PASSWORD,
            "college_name": "TAMUT",
        }
        api_client.post(SIGNUP_URL, signup, format="json")

        # Pull uid/token out of the link exactly as the user would click it.
        uid, token = re.search(r"/verify/([^/]+)/([^/\s]+)", mailoutbox[0].body).groups()
        response = api_client.get(verify_url(uid, token))

        assert response.status_code == 200
        assert response.data["detail"] == "Email verified. You can now log in."
        user = CustomUser.objects.get(username="sahil")
        assert user.is_active and user.is_edu_verified

        login = api_client.post(
            LOGIN_URL, {"school_email": "sahil@tamut.edu", "password": PASSWORD}, format="json"
        )
        assert login.status_code == 200

    def test_unverified_user_cannot_log_in(self, api_client, make_user):
        make_user(is_active=False)

        response = api_client.post(
            LOGIN_URL, {"school_email": "alice@tamut.edu", "password": PASSWORD}, format="json"
        )

        assert response.status_code == 400
        assert response.data["non_field_errors"] == [
            "Please verify your email before logging in."
        ]
        assert "token" not in response.data

    def test_tampered_token_is_rejected(self, api_client, make_user):
        user = make_user(is_active=False)
        uid, _ = link_parts(user)

        response = api_client.get(verify_url(uid, "abc123-not-a-real-token"))

        assert response.status_code == 400
        user.refresh_from_db()
        assert user.is_active is False

    def test_token_for_another_user_is_rejected(self, api_client, make_user):
        alice = make_user(is_active=False)
        bob = make_user(username="bob", school_email="bob@tamut.edu", is_active=False)
        _, alice_token = link_parts(alice)
        bob_uid, _ = link_parts(bob)

        response = api_client.get(verify_url(bob_uid, alice_token))

        assert response.status_code == 400
        bob.refresh_from_db()
        assert bob.is_active is False

    @pytest.mark.parametrize("uid", ["!!!", "OTk5OTk", "YWJj"])  # garbage, id 99999, "abc"
    def test_bad_uid_is_rejected(self, api_client, uid):
        response = api_client.get(verify_url(uid, "abc123-whatever"))

        assert response.status_code == 400
        assert response.data["detail"] == "Invalid or expired verification link."

    def test_already_verified(self, api_client, make_user):
        user = make_user(is_active=True, is_edu_verified=True)
        uid, token = link_parts(user)

        response = api_client.get(verify_url(uid, token))

        assert response.status_code == 200
        assert response.data["detail"] == "Email already verified."

    def test_old_link_cannot_reactivate_banned_user(self, api_client, make_user):
        # Verified, then deactivated by an admin.
        user = make_user(is_active=False, is_edu_verified=True)
        uid, token = link_parts(user)

        api_client.get(verify_url(uid, token))

        user.refresh_from_db()
        assert user.is_active is False

    def test_link_stops_working_after_first_login(self, api_client, make_user):
        user = make_user(is_active=False)
        uid, token = link_parts(user)
        api_client.get(verify_url(uid, token))
        api_client.post(
            LOGIN_URL, {"school_email": "alice@tamut.edu", "password": PASSWORD}, format="json"
        )

        response = api_client.get(verify_url(uid, token))

        # last_login changed, so the token no longer matches.
        assert response.status_code == 400
