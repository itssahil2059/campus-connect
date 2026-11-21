"""URLs for the UI tests: the real app plus /media/ for uploaded photos.

Tests run with DEBUG off, so core/urls.py doesn't serve media there (in
production Nginx does). The photo UI test switches ROOT_URLCONF to this.
"""

from django.conf import settings
from django.urls import re_path
from django.views.static import serve

from core.urls import urlpatterns as app_urlpatterns

urlpatterns = app_urlpatterns + [
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]
