from django.conf import settings
from django.db import models
from django.db.models import Q

MAX_MESSAGE_LENGTH = 2000


class ConversationQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(Q(user_a=user) | Q(user_b=user))


class Conversation(models.Model):
    """A private one-to-one chat between two students.

    The pair is stored in a fixed order (user_a has the smaller id), so "the
    chat between Alice and Bob" is one unique row no matter who opens it.
    """

    user_a = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    user_b = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # Bumped on every new message, so the chat list sorts by latest activity.
    updated_at = models.DateTimeField(auto_now=True)

    objects = ConversationQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user_a", "user_b"], name="one_conversation_per_pair"),
            models.CheckConstraint(
                condition=Q(user_a__lt=models.F("user_b")), name="conversation_users_ordered"
            ),
        ]

    def __str__(self):
        return f"{self.user_a} & {self.user_b}"

    @classmethod
    def get_or_create_between(cls, a, b):
        """Returns (conversation, created) for this pair, in either order."""
        first, second = sorted([a, b], key=lambda u: u.id)
        return cls.objects.get_or_create(user_a=first, user_b=second)

    def has_participant(self, user):
        return user.id in (self.user_a_id, self.user_b_id)

    def other_user(self, user):
        return self.user_b if self.user_a_id == user.id else self.user_a


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    body = models.TextField(max_length=MAX_MESSAGE_LENGTH)
    created_at = models.DateTimeField(auto_now_add=True)
    # Set when the other person reads it; null = unread.
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["id"]
        # History and polling both filter by conversation and page by id.
        indexes = [models.Index(fields=["conversation", "id"])]

    def __str__(self):
        return f"{self.sender}: {self.body[:40]}"
