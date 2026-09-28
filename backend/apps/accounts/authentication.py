from django.core.cache import cache
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class RevocableJWTAuthentication(JWTAuthentication):
    """Rejeita access tokens explicitamente revogados durante o logout."""

    def get_user(self, validated_token):
        jti = validated_token.get('jti')
        if jti and cache.get(f'revoked_access:{jti}'):
            raise AuthenticationFailed('Sessão encerrada.', code='token_revoked')
        user_id = validated_token.get('user_id')
        issued_at = validated_token.get('iat')
        valid_after = cache.get(f'user_tokens_valid_after:{user_id}') if user_id else None
        if valid_after and issued_at and int(issued_at) <= int(valid_after):
            raise AuthenticationFailed('Sessão encerrada após alteração de senha.', code='password_changed')
        return super().get_user(validated_token)
