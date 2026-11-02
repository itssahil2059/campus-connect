"""WebSocket login using the same DRF token as the REST API.

Browsers can't set an Authorization header on a WebSocket, so the frontend
connects to /ws/chat/<id>/?token=<token>. Nginx and Daphne access logs are
turned off for these requests so tokens don't end up in log files.
"""
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token


@database_sync_to_async
def get_user_for_token(key):
    token = Token.objects.select_related("user").filter(key=key).first()
    if token is None or not token.user.is_active:
        return AnonymousUser()
    return token.user


class TokenAuthMiddleware(BaseMiddleware):
    """Sets scope["user"] from ?token=, or AnonymousUser if missing/invalid."""

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode())
        key = (query.get("token") or [""])[0]
        scope["user"] = await get_user_for_token(key) if key else AnonymousUser()
        return await super().__call__(scope, receive, send)
