from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .emails import send_verification_email
from .serializers import SignupSerializer, UserPublicSerializer


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
