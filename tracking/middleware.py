from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def _user_from_token(raw_token: str):
    from accounts.models import User
    try:
        payload = AccessToken(raw_token)
        return User.objects.get(id=payload["user_id"])
    except (InvalidToken, TokenError, User.DoesNotExist, KeyError):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """Extracts a JWT access token from the ?token= query param and populates scope["user"].

    Browsers cannot send Authorization headers on WebSocket upgrades, so the
    token is passed as a query parameter instead. The access token is short-lived
    (10 min) which limits the exposure window for a captured token in a URL.
    """

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            qs = scope.get("query_string", b"").decode()
            params = parse_qs(qs)
            token_list = params.get("token", [])
            scope["user"] = (
                await _user_from_token(token_list[0]) if token_list else AnonymousUser()
            )
        return await super().__call__(scope, receive, send)
