from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Connection
from .serializers import ConnectionRequestSerializer, ConnectionSerializer

STATUS_FILTERS = {"connected", "incoming", "outgoing"}


class ConnectionViewSet(
    mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    """The logged-in user's connections and connection requests.

    GET    /api/connections/?status=connected|incoming|outgoing
    POST   /api/connections/                  {"user_id": 5}
    POST   /api/connections/<id>/accept/
    POST   /api/connections/<id>/decline/
    DELETE /api/connections/<id>/             cancel a request / remove a connection
    GET    /api/connections/with/<user_id>/   status with one student (profile button)
    """

    serializer_class = ConnectionSerializer

    def get_queryset(self):
        """Every row the user is allowed to see.

        A request you declined disappears for you; the sender keeps seeing it
        as "outgoing", so nobody is told they were turned down.
        """
        me = self.request.user
        qs = (
            Connection.objects.involving(me)
            .exclude(to_user=me, status=Connection.Status.DECLINED)
            .select_related("from_user__profile", "to_user__profile")
            .order_by("-created_at")
        )

        wanted = self.request.query_params.get("status")
        if self.action == "list" and wanted in STATUS_FILTERS:
            accepted = Q(status=Connection.Status.ACCEPTED)
            if wanted == "connected":
                qs = qs.filter(accepted)
            elif wanted == "incoming":
                qs = qs.filter(to_user=me).exclude(accepted)
            else:
                qs = qs.filter(from_user=me).exclude(accepted)
        return qs

    def create(self, request):
        serializer = ConnectionRequestSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        target = serializer.context["target"]

        try:
            with transaction.atomic():
                connection, created = self._send_request(request.user, target)
        except IntegrityError:
            # Both users clicked "Connect" at the same instant and the other
            # insert won. Run again: it now finds that row.
            connection, created = self._send_request(request.user, target)

        return Response(
            ConnectionSerializer(connection, context={"request": request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @staticmethod
    def _send_request(me, target):
        """Returns (connection, created). Safe to call repeatedly."""
        existing = Connection.objects.between(me, target).first()

        if existing is None:
            return Connection.objects.create(from_user=me, to_user=target), True

        if existing.status == Connection.Status.ACCEPTED or existing.from_user_id == me.id:
            # Already connected, or already asked: nothing changes.
            return existing, False

        if existing.status == Connection.Status.PENDING:
            # They already asked me, so asking back means yes.
            existing.status = Connection.Status.ACCEPTED
            existing.responded_at = timezone.now()
            existing.save(update_fields=["status", "responded_at"])
            return existing, False

        # I declined them earlier and changed my mind: turn it into my request.
        existing.from_user, existing.to_user = me, target
        existing.status = Connection.Status.PENDING
        existing.responded_at = None
        existing.save(update_fields=["from_user", "to_user", "status", "responded_at"])
        return existing, True

    def _respond(self, request, new_status):
        connection = self.get_object()
        if (
            connection.to_user_id != request.user.id
            or connection.status != Connection.Status.PENDING
        ):
            return Response(
                {"detail": "Only pending requests sent to you can be answered."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        connection.status = new_status
        connection.responded_at = timezone.now()
        connection.save(update_fields=["status", "responded_at"])
        return connection

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        result = self._respond(request, Connection.Status.ACCEPTED)
        if isinstance(result, Response):
            return result
        return Response(self.get_serializer(result).data)

    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        result = self._respond(request, Connection.Status.DECLINED)
        if isinstance(result, Response):
            return result
        return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, pk=None):
        connection = self.get_object()
        if (
            connection.to_user_id == request.user.id
            and connection.status == Connection.Status.PENDING
        ):
            # Deleting would let the sender ask again right away; decline
            # keeps the row so that can't happen.
            return Response(
                {"detail": "Use decline for requests sent to you."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        connection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path=r"with/(?P<user_id>\d+)")
    def with_user(self, request, user_id=None):
        """Status with one student, for the button on their profile."""
        connection = None
        if int(user_id) != request.user.id:
            # The queryset already involves me, so matching either side
            # finds the row for this pair.
            connection = (
                self.get_queryset()
                .filter(Q(from_user_id=user_id) | Q(to_user_id=user_id))
                .first()
            )
        if connection is None:
            return Response({"status": "none", "connection": None})
        data = self.get_serializer(connection).data
        return Response({"status": data["status"], "connection": data})
