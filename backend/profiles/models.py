from django.conf import settings
from django.db import models
from django.utils import timezone


def age_on(born, today):
    """Whole years between born and today (birthday not reached yet -> one less)."""
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


class Profile(models.Model):
    """What other students see about a user. One per user, created on setup."""

    class Gender(models.TextChoices):
        WOMAN = "woman", "Woman"
        MAN = "man", "Man"
        NON_BINARY = "non_binary", "Non-binary"
        OTHER = "other", "Other"
        PREFER_NOT_TO_SAY = "prefer_not_to_say", "Prefer not to say"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    bio = models.TextField(max_length=500, blank=True)
    # Private: other students only ever see the age worked out from it.
    # Nullable so profiles made before this field existed stay valid; the
    # API requires it on every save (see MyProfileSerializer).
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)
    city = models.CharField(max_length=100, blank=True)
    # Short lowercase tags, e.g. ["hiking", "coding"]. JSON lists keep this
    # simple for the prototype and can still be filtered in Postgres later.
    interests = models.JSONField(default=list, blank=True)
    likes = models.JSONField(default=list, blank=True)
    dislikes = models.JSONField(default=list, blank=True)
    # Up to 5 http(s) URLs: LinkedIn, GitHub, Instagram, a portfolio, etc.
    links = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user}"

    @property
    def age(self):
        if self.date_of_birth is None:
            return None
        return age_on(self.date_of_birth, timezone.localdate())


class Question(models.Model):
    """A multiple-choice preference question in the questionnaire."""

    text = models.CharField(max_length=255)
    choices = models.JSONField(default=list)  # list of strings
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.text


class Answer(models.Model):
    """A user's chosen option for one question (one answer per question)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="answers"
    )
    choice = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "question"], name="one_answer_per_question"
            )
        ]

    def __str__(self):
        return f"{self.user}: {self.question} -> {self.choice}"
