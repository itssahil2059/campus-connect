from django.contrib.auth import get_user_model
from django.db.models import Count, Max, Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from connections.models import Connection, are_connected

from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    MessageSerializer,
    StartConversationSerializer,
)
from .services import NotAllowed, mark_read, send_message

User = get_user_model()

PAGE_SIZE = 50


class SendMessageThrottle(ScopedRateThrottle):
    """Rate-limits sending only (reading history/polling isn't limited)."""

    def allow_request(self, request, view):
        if request.method != "POST" or getattr(view, "action", None) != "messages":
            return True
        return super().allow_request(request, view)


class ConversationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """The logged-in user's private chats.

    GET  /api/conversations/                         my chats, latest activity first
    POST /api/conversations/        {"user_id": 5}   open (or reuse) a chat with a connection
    GET  /api/conversations/<id>/                    one chat
    GET  /api/conversations/<id>/messages/?after=&before=
    POST /api/conversations/<id>/messages/  {"body": "hi"}
    POST /api/conversations/<id>/read/               mark their messages read
    """

    serializer_class = ConversationSerializer
    throttle_classes = [SendMessageThrottle]
    throttle_scope = "chat_send"

    def get_queryset(self):
        me = self.request.user
        return (
            Conversation.objects.for_user(me)
            .select_related("user_a__profile", "user_b__profile")
            .annotate(
                last_message_id=Max("messages__id"),
                unread_count=Count(
                    "messages",
                    filter=Q(messages__read_at__isnull=True) & ~Q(messages__sender=me),
                ),
            )
            .order_by("-updated_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        me = self.request.user
        accepted = Connection.objects.involving(me).filter(status=Connection.Status.ACCEPTED)
        context["connected_ids"] = {
            uid
            for pair in accepted.values_list("from_user_id", "to_user_id")
            for uid in pair
            if uid != me.id
        }
        return context

    def _serialize(self, conversations, many=False):
        items = conversations if many else [conversations]
        context = self.get_serializer_context()
        # One query for every chat's latest message.
        context["last_messages"] = Message.objects.in_bulk(
            [c.last_message_id for c in items if c.last_message_id]
        )
        return ConversationSerializer(conversations, many=many, context=context).data

    def list(self, request):
        return Response(self._serialize(list(self.get_queryset()), many=True))

    def retrieve(self, request, pk=None):
        return Response(self._serialize(self.get_object()))

    def create(self, request):
        serializer = StartConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        other = User.objects.filter(id=serializer.validated_data["user_id"]).first()
        if other is None or other == request.user:
            raise ValidationError({"user_id": ["No student with this id."]})
        if not are_connected(request.user, other):
            raise PermissionDenied("You can only message your connections.")

        conversation, created = Conversation.get_or_create_between(request.user, other)
        return Response(
            self._serialize(self.get_queryset().get(pk=conversation.pk)),
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get", "post"])
    def messages(self, request, pk=None):
        conversation = self.get_object()  # 404 unless it's one of my chats
        if request.method == "POST":
            return self._send(request, conversation)
        return self._history(request, conversation)

    def _history(self, request, conversation):
        """Messages oldest-first, paged by message id.

        ?after=<id>   newer than this (polling: pass the last id you have)
        ?before=<id>  older than this (scrolling up)
        neither       the latest page
        """
        after = self._int_param(request, "after")
        before = self._int_param(request, "before")
        messages = conversation.messages.all()

        if after is not None:
            page = list(messages.filter(id__gt=after).order_by("id")[: PAGE_SIZE + 1])
            has_more = len(page) > PAGE_SIZE
            page = page[:PAGE_SIZE]
        else:
            if before is not None:
                messages = messages.filter(id__lt=before)
            page = list(messages.order_by("-id")[: PAGE_SIZE + 1])
            has_more = len(page) > PAGE_SIZE
            page = page[:PAGE_SIZE][::-1]  # back to oldest-first

        return Response({"results": MessageSerializer(page, many=True).data, "has_more": has_more})

    @staticmethod
    def _int_param(request, name):
        value = request.query_params.get(name)
        if value is None:
            return None
        if not value.isdigit():
            raise ValidationError({name: ["Must be a message id."]})
        return int(value)

    def _send(self, request, conversation):
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            message = send_message(conversation, request.user, serializer.validated_data["body"])
        except NotAllowed as exc:
            raise PermissionDenied(str(exc))
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        mark_read(self.get_object(), request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
