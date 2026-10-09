from django.conf import settings
from django.db import models


class Profile(models.Model):
    """What other students see about a user. One per user, created on setup."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    bio = models.TextField(max_length=500, blank=True)
    # Short lowercase tags, e.g. ["hiking", "coding"]. JSON lists keep this
    # simple for the prototype and can still be filtered in Postgres later.
    interests = models.JSONField(default=list, blank=True)
    likes = models.JSONField(default=list, blank=True)
    dislikes = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user}"


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
