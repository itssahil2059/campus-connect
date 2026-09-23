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
        }

    def validate_school_email(self, value):
        # Runs after DRF's own field checks (valid email format, etc.).
        value = value.lower()

        if not value.endswith(".edu"):
            raise serializers.ValidationError("Please use your .edu school email.")

        # The model's unique=True is case-sensitive, and DRF's built-in unique
        # check runs before this method, so "A@x.edu" would slip past it when
        # "a@x.edu" already exists. Check again case-insensitively.
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
        # go through **extra_fields. New accounts start unverified; the
        # email-verification step flips is_edu_verified later.
        return CustomUser.objects.create_user(
            password=password,
            is_edu_verified=False,
            **validated_data,
        )


class UserPublicSerializer(serializers.ModelSerializer):
    """What the signup response returns: no password, no internal flags."""

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
