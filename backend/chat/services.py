"""Chat actions shared by the REST API and the WebSocket consumer.

Keeping "send a message" and "mark read" in one place means both ways of
doing them apply the same rules, save the same data, and notify the same
live listeners.
"""
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
from rest_framework.fields import DateTimeField

from connections.models import are_connected

from .models import Conversation, Message
from .serializers import MessageSerializer

logger = logging.getLogger(__name__)


class NotAllowed(Exception):
    """The user may not send in this conversation (e.g. not connected)."""


def group_name(conversation_id):
    """Channels group that every open WebSocket for this chat joins."""
    return f"chat_{conversation_id}"


def broadcast(conversation_id, event):
    """Pushes an event to everyone connected to this chat's WebSocket.

    Best effort: the message is already saved, so if Redis is down we log it
    and polling clients still get it on their next request.
    """
    try:
        async_to_sync(get_channel_layer().group_send)(group_name(conversation_id), event)
    except Exception:
        logger.warning("Chat broadcast failed for conversation %s", conversation_id, exc_info=True)


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

    # "type" picks the consumer method: chat.message -> chat_message().
    broadcast(conversation.pk, {"type": "chat.message", "message": dict(MessageSerializer(message).data)})
    return message


def mark_read(conversation, reader):
    """Marks the other person's unread messages as read. Returns how many."""
    now = timezone.now()
    count = (
        conversation.messages.filter(read_at__isnull=True)
        .exclude(sender=reader)
        .update(read_at=now)
    )
    if count:
        # Lets the sender's open chat show "Seen".
        broadcast(
            conversation.pk,
            {"type": "chat.read", "reader_id": reader.id, "read_at": DateTimeField().to_representation(now)},
        )
    return count
