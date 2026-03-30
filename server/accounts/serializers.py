from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken


class TokenObtainSingleSessionSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(username=username, password=password)
        if user is None:
            raise serializers.ValidationError('Invalid username or password')

        # Enforce single-session: bump token_version, invalidating older tokens.
        user.token_version = int(user.token_version) + 1
        user.save(update_fields=['token_version'])

        refresh = RefreshToken.for_user(user)
        refresh['token_version'] = user.token_version
        refresh['role'] = getattr(user, 'role', None)

        access = refresh.access_token
        access['token_version'] = user.token_version
        access['role'] = getattr(user, 'role', None)

        return {
            'refresh': str(refresh),
            'access': str(access),
        }
