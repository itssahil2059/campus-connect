from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Connection

User = get_user_model()


class ConnectionUserSerializer(serializers.ModelSerializer):
    """The other person in a connection. Never includes their email."""

    # The frontend links to /profiles/<profile_id>; null if not set up yet.
    profile_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "college_name", "graduation_year", "profile_id"]
        read_only_fields = fields

    def get_profile_id(self, user):
        profile = getattr(user, "profile", None)
        return profile.id if profile else None


class ConnectionSerializer(serializers.ModelSerializer):
    """A connection as seen by the logged-in user (request.user)."""

    status = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = Connection
        fields = ["id", "status", "user", "created_at", "responded_at"]
        read_only_fields = fields

    def _me(self):
        return self.context["request"].user

    def get_status(self, connection):
        return connection.status_for(self._me())

    def get_user(self, connection):
        return ConnectionUserSerializer(connection.other_user(self._me())).data


class ConnectionRequestSerializer(serializers.Serializer):
    """Input for POST /api/connections/: who to send a request to."""

    user_id = serializers.IntegerField()

    def validate_user_id(self, value):
        me = self.context["request"].user
        if value == me.id:
            raise serializers.ValidationError("You can't connect with yourself.")
        # Same rule as the profile list: only active, verified students.
        target = User.objects.filter(
            id=value, is_active=True, is_edu_verified=True
        ).first()
        if target is None:
            raise serializers.ValidationError("No student with this id.")
        self.context["target"] = target
        return value
