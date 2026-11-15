from django.core.validators import URLValidator
from rest_framework import serializers

from .models import Answer, Profile, Question

MAX_TAGS = 15
MAX_LINKS = 5


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

    class Meta:
        model = Profile
        fields = ["id", "bio", "interests", "likes", "dislikes", "links", "updated_at"]
        read_only_fields = ["id", "updated_at"]


class PublicProfileSerializer(serializers.ModelSerializer):
    """Another student's profile as shown on Home. Never includes their email."""

    # Needed to send a connection request or open a chat with this student.
    user_id = serializers.IntegerField(source="user.id")
    username = serializers.CharField(source="user.username")
    college_name = serializers.CharField(source="user.college_name")
    graduation_year = serializers.IntegerField(source="user.graduation_year")

    class Meta:
        model = Profile
        fields = [
            "id",
            "user_id",
            "username",
            "college_name",
            "graduation_year",
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
