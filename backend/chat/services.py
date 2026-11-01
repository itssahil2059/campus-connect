"""Chat actions shared by the REST API and (later) the WebSocket consumer.

Keeping the "send a message" logic in one place means both ways of sending
apply the same rules and produce the same result.
"""
from django.utils import timezone

from connections.models import are_connected

from .models import Conversation, Message


class NotAllowed(Exception):
    """The user may not send in this conversation (e.g. not connected)."""


def send_message(conversation, sender, body):
    """Saves a message after checking the sender may still use this chat.

    `body` must already be validated (non-empty, within the length limit).
    """
    if not conversation.has_participant(sender):
        raise NotAllowed("You're not part of this conversation.")
    if not are_connected(conversation.user_a, conversation.user_b):
        raise NotAllowed("You can only message your connections.")

    message = Message.objects.create(conversation=conversation, sender=sender, body=body)
    # Moves the chat to the top of both people's lists.
    Conversation.objects.filter(pk=conversation.pk).update(updated_at=message.created_at)
    return message


def mark_read(conversation, reader):
    """Marks the other person's unread messages as read. Returns how many."""
    return (
        conversation.messages.filter(read_at__isnull=True)
        .exclude(sender=reader)
        .update(read_at=timezone.now())
    )
