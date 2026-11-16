from datetime import date, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from profiles.models import Answer, Profile, Question

ME_URL = reverse("profiles:my-profile")
LIST_URL = reverse("profiles:profile-list")
QUESTIONS_URL = reverse("profiles:question-list")
ANSWERS_URL = reverse("profiles:answers")

PROFILE_DATA = {
    "bio": "CS junior, coffee addict.",
    "date_of_birth": "2004-03-15",
    "gender": "woman",
    "city": "Texarkana",
    "interests": ["hiking", "coding"],
    "likes": ["tacos"],
    "dislikes": ["early classes"],
}


@pytest.fixture
def alice(make_user):
    return make_user(is_edu_verified=True)


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

    def test_links_are_cleaned(self, client_for, alice):
        links = [" github.com/alice ", "https://github.com/alice", "", "http://alice.dev"]

        response = client_for(alice).put(ME_URL, {**PROFILE_DATA, "links": links}, format="json")

        assert response.status_code == 201
        assert response.data["links"] == ["https://github.com/alice", "http://alice.dev"]

    @pytest.mark.parametrize("bad", ["javascript:alert(1)", "ftp://files.example.com", "not a url"])
    def test_bad_links_rejected(self, client_for, alice, bad):
        response = client_for(alice).put(ME_URL, {**PROFILE_DATA, "links": [bad]}, format="json")

        assert response.status_code == 400
        assert "links" in response.data

    def test_too_many_links_rejected(self, client_for, alice):
        links = [f"https://site{i}.com" for i in range(6)]

        response = client_for(alice).put(ME_URL, {**PROFILE_DATA, "links": links}, format="json")

        assert response.status_code == 400

    def test_requires_login(self, api_client):
        assert api_client.get(ME_URL).status_code == 401
        assert api_client.put(ME_URL, PROFILE_DATA, format="json").status_code == 401

    def test_own_profile_returns_date_of_birth(self, client_for, alice):
        client = client_for(alice)
        client.put(ME_URL, PROFILE_DATA, format="json")

        data = client.get(ME_URL).data

        assert (data["date_of_birth"], data["gender"], data["city"]) == ("2004-03-15", "woman", "Texarkana")

    def test_date_of_birth_is_required(self, client_for, alice):
        data = {k: v for k, v in PROFILE_DATA.items() if k != "date_of_birth"}

        response = client_for(alice).put(ME_URL, data, format="json")

        assert response.status_code == 400
        assert "date_of_birth" in response.data

    def test_gender_and_city_are_optional(self, client_for, alice):
        data = {k: v for k, v in PROFILE_DATA.items() if k not in ("gender", "city")}

        assert client_for(alice).put(ME_URL, data, format="json").status_code == 201

    def test_under_18_rejected(self, client_for, alice):
        today = timezone.localdate()
        # Turns 18 tomorrow -> still 17 today.
        born = today.replace(year=today.year - 18) + timedelta(days=1)

        response = client_for(alice).put(ME_URL, {**PROFILE_DATA, "date_of_birth": born.isoformat()}, format="json")

        assert response.status_code == 400
        assert "at least 18" in str(response.data["date_of_birth"])

    def test_exactly_18_today_accepted(self, client_for, alice):
        today = timezone.localdate()
        born = date(today.year - 18, today.month, 28 if (today.month, today.day) == (2, 29) else today.day)

        response = client_for(alice).put(ME_URL, {**PROFILE_DATA, "date_of_birth": born.isoformat()}, format="json")

        assert response.status_code == 201

    @pytest.mark.parametrize("bad", ["2999-01-01", "1900-01-01", "not-a-date"])
    def test_impossible_dates_rejected(self, client_for, alice, bad):
        response = client_for(alice).put(ME_URL, {**PROFILE_DATA, "date_of_birth": bad}, format="json")

        assert response.status_code == 400
        assert "date_of_birth" in response.data

    def test_unknown_gender_rejected(self, client_for, alice):
        response = client_for(alice).put(ME_URL, {**PROFILE_DATA, "gender": "robot"}, format="json")

        assert response.status_code == 400
        assert "gender" in response.data


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
        assert response.data["user_id"] == bob.id
        assert response.data["interests"] == ["hiking", "coding"]
        assert "school_email" not in response.data
        assert "bob@tamut.edu" not in str(response.data)

    def test_public_profile_shows_age_not_date_of_birth(self, client_for, make_user, alice):
        bob = make_user(username="bob", school_email="bob@tamut.edu", is_edu_verified=True)
        profile = Profile.objects.create(user=bob, **{**PROFILE_DATA, "date_of_birth": date(2004, 3, 15)})

        data = client_for(alice).get(detail_url(profile)).data

        assert data["age"] == profile.age
        assert (data["gender"], data["city"]) == ("woman", "Texarkana")
        assert "date_of_birth" not in data
        assert "2004" not in str(data)

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


@pytest.mark.django_db
class TestProfileSearch:
    @pytest.fixture
    def students(self, make_user, alice):
        """Three other students with different colleges and tags."""

        def student(name, college, bio="", **tags):
            user = make_user(
                username=name, school_email=f"{name}@x.edu",
                college_name=college, is_edu_verified=True,
            )
            return Profile.objects.create(user=user, bio=bio, **tags)

        Profile.objects.create(user=alice, interests=["hiking"])  # never in results
        return {
            "sam": student("sam", "Texas A&M-Texarkana", "Night owl coder",
                           interests=["hiking", "coding"], likes=["coffee"]),
            "riya": student("riya", "Rice University", "Loves museums",
                            interests=["art", "hiking"], dislikes=["coffee"]),
            "leo": student("leo", "Texas A&M-Texarkana",
                           interests=["gaming"], likes=["coffee", "tacos"]),
        }

    def search(self, client_for, alice, params):
        response = client_for(alice).get(LIST_URL, params)
        assert response.status_code == 200
        return sorted(p["username"] for p in response.data)

    @pytest.mark.parametrize("params, expected", [
        ({}, ["leo", "riya", "sam"]),
        ({"q": "SAM"}, ["sam"]),                      # username, any case
        ({"q": "rice"}, ["riya"]),                    # college
        ({"q": "museum"}, ["riya"]),                  # bio
        ({"college": "texarkana"}, ["leo", "sam"]),
        ({"interest": "Hiking"}, ["riya", "sam"]),    # tags are lowercased
        ({"interest": ["hiking", "coding"]}, ["sam"]),  # must have all
        ({"like": "coffee"}, ["leo", "sam"]),
        ({"dislike": "coffee"}, ["riya"]),
        ({"college": "texarkana", "like": "tacos"}, ["leo"]),  # filters combine
        ({"interest": "hik"}, []),                    # tags match exactly, not partly
        ({"q": "   "}, ["leo", "riya", "sam"]),       # blank params are ignored
    ])
    def test_filters(self, client_for, alice, students, params, expected):
        assert self.search(client_for, alice, params) == expected

    def test_never_includes_yourself(self, client_for, alice, students):
        assert "alice" not in self.search(client_for, alice, {"interest": "hiking"})

    def test_detail_ignores_filters(self, client_for, alice, students):
        url = detail_url(students["leo"])
        assert client_for(alice).get(url, {"q": "nobody"}).status_code == 200


@pytest.mark.django_db
class TestProfileBasicsSearch:
    """Search by city, gender and age range."""

    @pytest.fixture
    def students(self, make_user, alice):
        today = timezone.localdate()

        def student(name, age, gender, city):
            user = make_user(username=name, school_email=f"{name}@x.edu", is_edu_verified=True)
            # Birthday was yesterday, so they're exactly `age` (no edge cases here).
            born = (today - timedelta(days=1)).replace(year=today.year - age)
            Profile.objects.create(user=user, date_of_birth=born, gender=gender, city=city)

        student("ana", 19, "woman", "Texarkana")
        student("ben", 22, "man", "Dallas")
        student("cam", 25, "non_binary", "Texarkana")
        user = make_user(username="dee", school_email="dee@x.edu", is_edu_verified=True)
        Profile.objects.create(user=user)  # older profile with no age/city yet

    @pytest.mark.parametrize("params, expected", [
        ({"city": "texar"}, ["ana", "cam"]),
        ({"gender": "man"}, ["ben"]),
        ({"min_age": 22}, ["ben", "cam"]),           # inclusive
        ({"max_age": 22}, ["ana", "ben"]),           # inclusive
        ({"min_age": 20, "max_age": 24}, ["ben"]),
        ({"city": "texarkana", "gender": "woman"}, ["ana"]),
        ({"min_age": "abc"}, ["ana", "ben", "cam", "dee"]),  # junk ignored
    ])
    def test_filters(self, client_for, alice, students, params, expected):
        response = client_for(alice).get(LIST_URL, params)

        assert sorted(p["username"] for p in response.data) == expected
