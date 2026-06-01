from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def get_user_from_token(token):
    """JWT token (query-string'dagi ?token=) bo'yicha foydalanuvchini qaytaradi.
    Token yaroqsiz bo'lsa AnonymousUser qaytariladi."""
    from rest_framework_simplejwt.authentication import JWTAuthentication
    from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

    auth = JWTAuthentication()
    try:
        validated = auth.get_validated_token(token)
        return auth.get_user(validated)
    except (TokenError, InvalidToken, KeyError):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """WebSocket scope'iga JWT orqali foydalanuvchini biriktiradi.
    Token query-string orqali keladi, chunki brauzer ws ulanishida
    Authorization header yuborolmaydi."""

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get('query_string', b'').decode())
        token = query.get('token', [None])[0]
        scope['user'] = await get_user_from_token(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)
