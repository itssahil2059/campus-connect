from django.contrib.auth import get_user_model
from rest_framework import serializers

from connections.serializers import ConnectionUserSerializer

from .models import MAX_MESSAGE_LENGTH, Conversation, Message

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    """One message. Same shape over REST and (later) the WebSocket."""

    conversation_id = serializers.IntegerField(read_only=True)
    sender_id = serializers.IntegerField(read_only=True)
    # trim_whitespace (on by default) + allow_blank=False rejects "   ".
    body = serializers.CharField(max_length=MAX_MESSAGE_LENGTH)

    class Meta:
        model = Message
        fields = ["id", "conversation_id", "sender_id", "body", "created_at", "read_at"]
        read_only_fields = ["id", "conversation_id", "sender_id", "created_at", "read_at"]


class ConversationSerializer(serializers.ModelSerializer):
    """A conversation as seen by the logged-in user.

    Expects these to be set up by the view (so the list costs a fixed number
    of queries, not one per chat):
      - annotations `unread_count` and `last_message_id` on each conversation
      - context["last_messages"]: {message_id: Message}
      - context["connected_ids"]: set of user ids the viewer is connected to
    """

    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.IntegerField(read_only=True)
    is_connected = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "other_user", "last_message", "unread_count", "is_connected", "updated_at"]
        read_only_fields = fields

    def _other(self, conversation):
        return conversation.other_user(self.context["request"].user)

    def get_other_user(self, conversation):
        return ConnectionUserSerializer(self._other(conversation)).data

    def get_last_message(self, conversation):
        message = self.context["last_messages"].get(conversation.last_message_id)
        return MessageSerializer(message).data if message else None

    def get_is_connected(self, conversation):
        # False = history stays readable but sending is blocked.
        return self._other(conversation).id in self.context["connected_ids"]


class StartConversationSerializer(serializers.Serializer):
    """Input for POST /api/conversations/."""

    user_id = serializers.IntegerField()
