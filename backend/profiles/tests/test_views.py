import pytest
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from profiles.models import Answer, Profile, Question

ME_URL = reverse("profiles:my-profile")
LIST_URL = reverse("profiles:profile-list")
QUESTIONS_URL = reverse("profiles:question-list")
ANSWERS_URL = reverse("profiles:answers")

PROFILE_DATA = {
    "bio": "CS junior, coffee addict.",
    "interests": ["hiking", "coding"],
    "likes": ["tacos"],
    "dislikes": ["early classes"],
}


@pytest.fixture
def alice(make_user):
    return make_user(is_edu_verified=True)


@pytest.fixture
def client_for():
    """Returns an API client already logged in as the given user."""
    def _client_for(user):
        client = APIClient()
        token, _ = Token.objects.get_or_create(user=user)
        client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        return client

    return _client_for


def detail_url(profile):
    return reverse("profiles:profile-detail", kwargs={"pk": profile.pk})


@pytest.mark.django_db
class TestMyProfile:
    def test_get_is_404_before_setup(self, client_for, alice):
        assert client_for(alice).get(ME_URL).status_code == 404

    def test_put_creates_then_updates(self, client_for, alice):
        client = client_for(alice)

        created = client.put(ME_URL, PROFILE_DATA, format="json")
        updated = client.put(ME_URL, {**PROFILE_DATA, "bio": "New bio"}, format="json")

        assert created.status_code == 201
        assert updated.status_code == 200
        assert Profile.objects.filter(user=alice).count() == 1
        assert client.get(ME_URL).data["bio"] == "New bio"

    def test_tags_are_cleaned(self, client_for, alice):
        data = {**PROFILE_DATA, "interests": [" Hiking ", "hiking", "", "CODING"]}

        response = client_for(alice).put(ME_URL, data, format="json")

        assert response.data["interests"] == ["hiking", "coding"]

    def test_too_many_tags_rejected(self, client_for, alice):
        data = {**PROFILE_DATA, "interests": [f"tag{i}" for i in range(16)]}

        response = client_for(alice).put(ME_URL, data, format="json")

        assert response.status_code == 400
        assert "interests" in response.data

    def test_requires_login(self, api_client):
        assert api_client.get(ME_URL).status_code == 401
        assert api_client.put(ME_URL, PROFILE_DATA, format="json").status_code == 401


@pytest.mark.django_db
class TestProfileList:
    def test_lists_other_verified_users_only(self, client_for, make_user, alice):
        bob = make_user(username="bob", school_email="bob@tamut.edu", is_edu_verified=True)
        unverified = make_user(
            username="carol", school_email="carol@tamut.edu", is_active=False
        )
        banned = make_user(
            username="dan", school_email="dan@tamut.edu",
            is_active=False, is_edu_verified=True,
        )
        for user in (alice, bob, unverified, banned):
            Profile.objects.create(user=user, bio=f"I am {user.username}")

        response = client_for(alice).get(LIST_URL)

        assert response.status_code == 200
        assert [p["username"] for p in response.data] == ["bob"]

    def test_users_without_profile_not_listed(self, client_for, make_user, alice):
        make_user(username="bob", school_email="bob@tamut.edu", is_edu_verified=True)

        assert client_for(alice).get(LIST_URL).data == []

    def test_public_profile_hides_email(self, client_for, make_user, alice):
        bob = make_user(username="bob", school_email="bob@tamut.edu", is_edu_verified=True)
        profile = Profile.objects.create(user=bob, **PROFILE_DATA)

        response = client_for(alice).get(detail_url(profile))

        assert response.status_code == 200
        assert response.data["username"] == "bob"
        assert response.data["interests"] == ["hiking", "coding"]
        assert "school_email" not in response.data
        assert "bob@tamut.edu" not in str(response.data)

    def test_requires_login(self, api_client):
        assert api_client.get(LIST_URL).status_code == 401


@pytest.mark.django_db
class TestQuestionnaire:
    def test_starter_questions_are_loaded_in_order(self, client_for, alice):
        response = client_for(alice).get(QUESTIONS_URL)

        assert response.status_code == 200
        assert len(response.data) == 5
        assert response.data[0]["text"] == "What are you mainly looking for?"
        assert "Night owl" in response.data[3]["choices"]

    def test_save_and_read_answers(self, client_for, alice):
        q1, q2 = Question.objects.all()[:2]
        client = client_for(alice)

        response = client.post(
            ANSWERS_URL,
            [
                {"question": q1.id, "choice": q1.choices[0]},
                {"question": q2.id, "choice": q2.choices[1]},
            ],
            format="json",
        )

        assert response.status_code == 200
        assert len(client.get(ANSWERS_URL).data) == 2

    def test_changing_an_answer_replaces_it(self, client_for, alice):
        q = Question.objects.first()
        client = client_for(alice)

        client.post(ANSWERS_URL, [{"question": q.id, "choice": q.choices[0]}], format="json")
        client.post(ANSWERS_URL, [{"question": q.id, "choice": q.choices[1]}], format="json")

        answers = Answer.objects.filter(user=alice)
        assert answers.count() == 1
        assert answers.get().choice == q.choices[1]

    def test_invalid_choice_rejected_and_nothing_saved(self, client_for, alice):
        q1, q2 = Question.objects.all()[:2]

        response = client_for(alice).post(
            ANSWERS_URL,
            [
                {"question": q1.id, "choice": q1.choices[0]},
                {"question": q2.id, "choice": "Not an option"},
            ],
            format="json",
        )

        assert response.status_code == 400
        assert not Answer.objects.exists()

    def test_only_see_your_own_answers(self, client_for, make_user, alice):
        bob = make_user(username="bob", school_email="bob@tamut.edu")
        q = Question.objects.first()
        Answer.objects.create(user=bob, question=q, choice=q.choices[0])

        assert client_for(alice).get(ANSWERS_URL).data == []

    def test_requires_login(self, api_client):
        assert api_client.get(QUESTIONS_URL).status_code == 401
        assert api_client.get(ANSWERS_URL).status_code == 401
