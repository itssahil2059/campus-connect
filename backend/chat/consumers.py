import time
from collections import deque

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import Conversation
from .serializers import MessageSerializer
from .services import NotAllowed, group_name, mark_read, send_message

# Close codes the frontend can act on (4000-4999 are free for apps to use).
CLOSE_NOT_LOGGED_IN = 4401
CLOSE_NOT_IN_CHAT = 4403

# Same limit as the REST API: 60 messages per minute.
RATE_LIMIT = 60
RATE_WINDOW_SECONDS = 60


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """Live messages for one conversation: /ws/chat/<conversation_id>/

    Client -> server:  {"type": "message", "body": "hi"}
                       {"type": "read"}
    Server -> client:  {"type": "message", "message": {...}}
                       {"type": "read", "reader_id": 5, "read_at": "..."}
                       {"type": "error", "detail": "..."}

    Sending goes through chat.services, the same code as the REST API, so
    the rules (connected users only, length limit) are identical and a
    message sent over REST also shows up here.
    """

    async def connect(self):
        self.user = self.scope["user"]
        self.conversation_id = int(self.scope["url_route"]["kwargs"]["conversation_id"])
        self.group = group_name(self.conversation_id)
        self.recent_sends = deque()

        # Accept first, then close with a code: closing before accepting
        # makes the browser see a generic failure (1006) instead of our code.
        if not self.user.is_authenticated:
            await self.accept()
            await self.close(code=CLOSE_NOT_LOGGED_IN)
            return

        self.conversation = await self._get_conversation()
        if self.conversation is None:
            await self.accept()
            await self.close(code=CLOSE_NOT_IN_CHAT)
            return

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if getattr(self, "conversation", None) is not None:
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        kind = content.get("type") if isinstance(content, dict) else None
        if kind == "message":
            await self._handle_message(content)
        elif kind == "read":
            await database_sync_to_async(mark_read)(self.conversation, self.user)
        else:
            await self._error("Unknown message type.")

    async def _handle_message(self, content):
        if self._rate_limited():
            await self._error("You're sending messages too fast. Slow down.")
            return

        serializer = MessageSerializer(data={"body": content.get("body", "")})
        if not serializer.is_valid():
            await self._error(serializer.errors["body"][0])
            return

        try:
            # The broadcast inside send_message delivers it back to this
            # socket too, so the sender gets the saved message (with its id).
            await database_sync_to_async(send_message)(
                self.conversation, self.user, serializer.validated_data["body"]
            )
        except NotAllowed as exc:
            await self._error(str(exc))

    def _rate_limited(self):
        now = time.monotonic()
        while self.recent_sends and now - self.recent_sends[0] > RATE_WINDOW_SECONDS:
            self.recent_sends.popleft()
        if len(self.recent_sends) >= RATE_LIMIT:
            return True
        self.recent_sends.append(now)
        return False

    async def _error(self, detail):
        await self.send_json({"type": "error", "detail": str(detail)})

    @database_sync_to_async
    def _get_conversation(self):
        """The conversation, only if this user is in it."""
        return (
            Conversation.objects.for_user(self.user)
            .select_related("user_a", "user_b")
            .filter(pk=self.conversation_id)
            .first()
        )

    # --- Group events (sent by chat.services.broadcast) ---

    async def chat_message(self, event):
        await self.send_json({"type": "message", "message": event["message"]})

    async def chat_read(self, event):
        await self.send_json(
            {"type": "read", "reader_id": event["reader_id"], "read_at": event["read_at"]}
        )
