from django.core.validators import URLValidator
from django.utils import timezone
from rest_framework import serializers

from .models import Answer, Profile, Question, age_on

MAX_TAGS = 15
MAX_LINKS = 5
MIN_AGE = 18  # dating features: adults only
MAX_AGE = 100  # anything older is a typo


class TagListField(serializers.ListField):
    """A list of short tags, cleaned up: trimmed, lowercased, no blanks/duplicates."""

    child = serializers.CharField(max_length=40, allow_blank=True)

    def __init__(self, **kwargs):
        kwargs.setdefault("max_length", MAX_TAGS)
        kwargs.setdefault("required", False)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        tags = super().to_internal_value(data)
        cleaned = []
        for tag in tags:
            tag = tag.strip().lower()
            if tag and tag not in cleaned:
                cleaned.append(tag)
        return cleaned


class LinkListField(serializers.ListField):
    """Up to MAX_LINKS http(s) URLs, trimmed, blanks and duplicates dropped."""

    # Only http(s): rejects javascript: and other schemes, so links are safe
    # to render as <a href> on the frontend.
    child = serializers.URLField(
        max_length=200, validators=[URLValidator(schemes=["http", "https"])]
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("max_length", MAX_LINKS)
        kwargs.setdefault("required", False)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if isinstance(data, list):
            data = [u.strip() for u in data if isinstance(u, str) and u.strip()]
            # Students often type "github.com/sam"; assume https.
            data = [u if "://" in u else f"https://{u}" for u in data]
        links = super().to_internal_value(data)
        return list(dict.fromkeys(links))  # drop duplicates, keep order


class MyProfileSerializer(serializers.ModelSerializer):
    """The logged-in user's own profile (editable)."""

    interests = TagListField()
    likes = TagListField()
    dislikes = TagListField()
    links = LinkListField()
    # Required on every save, so older profiles get it the next time they edit.
    date_of_birth = serializers.DateField()
    city = serializers.CharField(max_length=100, required=False, allow_blank=True, trim_whitespace=True)

    class Meta:
        model = Profile
        fields = [
            "id", "bio", "date_of_birth", "gender", "city",
            "interests", "likes", "dislikes", "links", "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]
        extra_kwargs = {"gender": {"required": False}}

    def validate_date_of_birth(self, born):
        today = timezone.localdate()
        if born > today:
            raise serializers.ValidationError("Date of birth can't be in the future.")
        age = age_on(born, today)
        if age < MIN_AGE:
            raise serializers.ValidationError(f"You must be at least {MIN_AGE} to use Git Together.")
        if age > MAX_AGE:
            raise serializers.ValidationError("Please check your date of birth.")
        return born


class PublicProfileSerializer(serializers.ModelSerializer):
    """Another student's profile as shown on Home. Never includes their email."""

    # Needed to send a connection request or open a chat with this student.
    user_id = serializers.IntegerField(source="user.id")
    username = serializers.CharField(source="user.username")
    college_name = serializers.CharField(source="user.college_name")
    graduation_year = serializers.IntegerField(source="user.graduation_year")
    # Age only, never the date of birth itself.
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "user_id",
            "username",
            "college_name",
            "graduation_year",
            "age",
            "gender",
            "city",
            "bio",
            "interests",
            "likes",
            "dislikes",
            "links",
        ]
        read_only_fields = fields


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "text", "choices"]


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ["question", "choice"]
        # The view upserts by (user, question), so skip DRF's unique-together
        # check (it would reject changing an existing answer).
        validators = []

    def validate(self, attrs):
        if attrs["choice"] not in attrs["question"].choices:
            raise serializers.ValidationError(
                {"choice": f"Not a valid option for question {attrs['question'].id}."}
            )
        return attrs
