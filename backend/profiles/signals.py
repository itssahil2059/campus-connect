"""Delete a profile's photo files when the profile row is deleted.

Deleting a user account cascades to their Profile, so this also covers
account deletion (admin, shell, or a future "delete my account" endpoint).
"""

from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Profile
from .photos import delete_files


@receiver(post_delete, sender=Profile)
def delete_photo_files(sender, instance, **kwargs):
    names = (instance.photo.name, instance.photo_thumbnail.name)
    transaction.on_commit(lambda: delete_files(*names))
