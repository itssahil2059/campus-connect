from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def send_verification_email(request, user):
    """Email the user a link that activates their account (see VerifyEmailView)."""
    # uid: the user's id, base64-encoded so it's URL-safe (not secret).
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    # token: signed with SECRET_KEY, nothing stored in the DB. Expires after
    # PASSWORD_RESET_TIMEOUT (3 days by default).
    token = default_token_generator.make_token(user)

    # build_absolute_uri adds scheme + host, e.g. http://127.0.0.1:8000
    link = request.build_absolute_uri(f"/api/auth/verify/{uid}/{token}/")

    send_mail(
        subject="Verify your Git Together account",
        message=(
            f"Hi {user.username},\n\n"
            f"Click the link below to verify your school email:\n\n{link}\n\n"
            "If you didn't sign up, you can ignore this email."
        ),
        from_email=None,  # None = use DEFAULT_FROM_EMAIL from settings
        recipient_list=[user.school_email],
    )
