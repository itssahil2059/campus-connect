"""
ASGI entry point, served by Daphne in production (and by `runserver` in dev,
because 'daphne' is in INSTALLED_APPS).

HTTP requests go to Django as usual; WebSocket connections go through the
token login middleware to the chat consumer.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
# Set up Django before importing anything that touches models.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402

from chat.middleware import TokenAuthMiddleware  # noqa: E402
from chat.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    # The origin check rejects WebSockets opened by pages on other sites
    # (the browser always sends Origin; it must be in ALLOWED_HOSTS).
    'websocket': AllowedHostsOriginValidator(
        TokenAuthMiddleware(URLRouter(websocket_urlpatterns))
    ),
})
