from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Starter custom user model. Extend this during the data-model pass
    (e.g. quiz-answer fields for matching, safety/emergency contact,
    verification status/document reference).
    """
    school_email = models.EmailField(
        unique=True,
        help_text="Must be a verified .edu address.",
    )
    college_name = models.CharField(max_length=255, blank=True)
    graduation_year = models.PositiveIntegerField(null=True, blank=True)
    is_edu_verified = models.BooleanField(default=False)
    is_id_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.username
