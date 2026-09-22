from django.core.cache import cache
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class RevocableJWTAuthentication(JWTAuthentication):
    """Rejeita access tokens explicitamente revogados durante o logout."""

    def get_user(self, validated_token):
        jti = validated_token.get('jti')
        if jti and cache.get(f'revoked_access:{jti}'):
            raise AuthenticationFailed('Sessão encerrada.', code='token_revoked')
        return super().get_user(validated_token)
