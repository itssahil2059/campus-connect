"""
ASGI config. Once the chat app exists, add a websocket URLRouter here,
e.g.:

    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.auth import AuthMiddlewareStack
    from chat.routing import websocket_urlpatterns

    application = ProtocolTypeRouter({
        'http': django_asgi_app,
        'websocket': AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    })
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
application = get_asgi_application()
