from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class SingleSessionJWTAuthentication(JWTAuthentication):
    """JWT auth that enforces only one active login per user.

    We do this by embedding a `token_version` claim in tokens.
    When a user logs in, we increment `user.token_version`.
    Any previously issued tokens become invalid.
    """

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        token_version = validated_token.get('token_version')
        if token_version is None:
            raise AuthenticationFailed('Token missing token_version')
        if int(token_version) != int(user.token_version):
            raise AuthenticationFailed('Session expired (logged in elsewhere)')
        return user
