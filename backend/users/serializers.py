from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import CustomUser


class SignupSerializer(serializers.ModelSerializer):
    # Not a model field, so it has to be declared explicitly here.
    # write_only=True means it is accepted on input but never returned.
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "username",
            "school_email",
            "password",
            "password_confirm",
            "college_name",
            "graduation_year",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
            # The model allows a blank college_name; signup should not.
            "college_name": {"required": True, "allow_blank": False},
            # Drop DRF's auto-generated unique check (case-sensitive, generic
            # message). validate_school_email() does a case-insensitive check
            # instead; the DB unique constraint is still the final guard.
            "school_email": {"validators": []},
        }

    def validate_school_email(self, value):
        # Runs after DRF's own field checks (valid email format, etc.).
        value = value.lower()

        if not value.endswith(".edu"):
            raise serializers.ValidationError("Please use your .edu school email.")

        # Case-insensitive duplicate check, so "A@x.edu" is rejected when
        # "a@x.edu" already exists (the model's unique=True is case-sensitive).
        if CustomUser.objects.filter(school_email__iexact=value).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        return value

    def validate(self, attrs):
        # Cross-field checks live here because they need more than one field.
        # pop() removes password_confirm so it never reaches create().
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )

        # Passing an unsaved user lets Django's similarity validator reject
        # passwords that are too close to the username or email.
        candidate = CustomUser(
            username=attrs.get("username"),
            school_email=attrs.get("school_email"),
        )
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            # Re-raise as a DRF error keyed to "password" so the frontend can
            # show the messages next to the right input.
            raise serializers.ValidationError({"password": list(exc.messages)})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        # create_user() hashes the password. school_email, college_name, etc.
        # go through **extra_fields. New accounts start inactive and
        # unverified: Django's authenticate() refuses inactive users, so they
        # can't log in until the email-verification step flips both flags.
        return CustomUser.objects.create_user(
            password=password,
            is_active=False,
            is_edu_verified=False,
            **validated_data,
        )


class LoginSerializer(serializers.Serializer):
    # Plain Serializer (not ModelSerializer): login doesn't create or update a
    # model, it just validates input and finds the matching user.
    school_email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = CustomUser.objects.filter(
            school_email__iexact=attrs["school_email"]
        ).first()

        # Same message for "no such email" and "wrong password", so the
        # response doesn't reveal which one was wrong.
        if user is None or not user.check_password(attrs["password"]):
            raise serializers.ValidationError("Invalid email or password.")

        # Only reached with the correct password, so this message is safe.
        if not user.is_active:
            raise serializers.ValidationError(
                "Please verify your email before logging in."
            )

        # The view reads the user from serializer.validated_data["user"].
        attrs["user"] = user
        return attrs


class UserPublicSerializer(serializers.ModelSerializer):
    """Safe user data for API responses: no password, no internal flags."""

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "school_email",
            "college_name",
            "graduation_year",
            "is_edu_verified",
        ]
        read_only_fields = fields
