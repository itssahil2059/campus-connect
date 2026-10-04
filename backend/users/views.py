from django.contrib.auth.models import update_last_login
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from .emails import send_verification_email
from .models import CustomUser
from .serializers import LoginSerializer, SignupSerializer, UserPublicSerializer


class SignupView(generics.CreateAPIView):
    """POST /api/auth/signup/ — create an inactive, unverified account."""

    serializer_class = SignupSerializer

    # Settings default to IsAuthenticated, so signup must opt out explicitly.
    permission_classes = [permissions.AllowAny]
    # Also skip authentication. Otherwise a stale/invalid Authorization header
    # returns 401 before we get here, and a logged-in browser session would
    # trigger CSRF checks on this POST.
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_verification_email(request, user)

        # Respond with the public serializer, not SignupSerializer, so nothing
        # password-related is echoed back. No token yet: the user has to
        # verify their .edu email first.
        return Response(
            UserPublicSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    """GET /api/auth/verify/<uidb64>/<token>/ — activate the account."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request, uidb64, token):
        # Decode the uid back to a user id. Any garbage in the URL (bad
        # base64, non-numeric id, unknown user) ends up as user = None.
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=user_id)
        # (Same exception list Django's own password-reset view uses.)
        except (TypeError, ValueError, OverflowError, ValidationError,
                CustomUser.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid or expired verification link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check is_edu_verified, not is_active: an admin may deactivate a
        # verified user (a ban), and an old link must not undo that.
        if user.is_edu_verified:
            return Response({"detail": "Email already verified."})

        user.is_active = True
        user.is_edu_verified = True
        user.save(update_fields=["is_active", "is_edu_verified"])
        return Response({"detail": "Email verified. You can now log in."})


class LoginView(APIView):
    """POST /api/auth/login/ — exchange email + password for an auth token."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # One token per user: reuse it if they're already logged in elsewhere.
        token, _created = Token.objects.get_or_create(user=user)
        # Token login doesn't set last_login on its own. Updating it also
        # invalidates any outstanding verification link for this user.
        update_last_login(None, user)

        return Response({"token": token.key, "user": UserPublicSerializer(user).data})


class LogoutView(APIView):
    """POST /api/auth/logout/ — delete the user's token (default: must be logged in)."""

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(generics.RetrieveAPIView):
    """GET /api/auth/me/ — the currently logged-in user."""

    serializer_class = UserPublicSerializer

    def get_object(self):
        # No lookup by id: "me" is always whoever the token belongs to.
        return self.request.user
