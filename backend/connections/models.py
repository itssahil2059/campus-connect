from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.functions import Greatest, Least


class ConnectionQuerySet(models.QuerySet):
    def involving(self, user):
        """Rows where the user is either side."""
        return self.filter(Q(from_user=user) | Q(to_user=user))

    def between(self, a, b):
        """The (at most one) row for this pair, in either direction."""
        return self.filter(
            Q(from_user=a, to_user=b) | Q(from_user=b, to_user=a)
        )


class Connection(models.Model):
    """A connection request between two students, and its outcome.

    There is at most one row per pair of users (in either direction). Only
    the two people involved can ever see it: connections are private.
    """

    class Status(models.TextChoices):
        PENDING = "pending"
        ACCEPTED = "accepted"
        DECLINED = "declined"

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="connections_sent",
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="connections_received",
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    objects = ConnectionQuerySet.as_manager()

    class Meta:
        constraints = [
            # LEAST/GREATEST make the pair order-independent, so A->B and
            # B->A can't both exist. Enforced by Postgres, not just Python.
            models.UniqueConstraint(
                Least("from_user", "to_user"),
                Greatest("from_user", "to_user"),
                name="one_connection_per_pair",
            ),
            models.CheckConstraint(
                condition=~Q(from_user=models.F("to_user")),
                name="no_self_connection",
            ),
        ]
        indexes = [models.Index(fields=["to_user", "status"])]

    def __str__(self):
        return f"{self.from_user} -> {self.to_user} ({self.status})"

    def other_user(self, user):
        return self.to_user if self.from_user_id == user.id else self.from_user

    def status_for(self, user):
        """How this row looks to `user`: connected / incoming / outgoing.

        A declined request still looks "outgoing" (pending) to the sender, so
        the app never tells anyone they were turned down.
        """
        if self.status == self.Status.ACCEPTED:
            return "connected"
        return "outgoing" if self.from_user_id == user.id else "incoming"


def are_connected(a, b):
    """True if the two users have an accepted connection. Used by chat."""
    return Connection.objects.between(a, b).filter(
        status=Connection.Status.ACCEPTED
    ).exists()
