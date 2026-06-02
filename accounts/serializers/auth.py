from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs['phone_number'], password=attrs['password'])
        # O'chirilgan (soft-deleted) akkount ham kira olmasligi kerak.
        if not user or user.deleted_at is not None:
            raise serializers.ValidationError("Telefon raqam yoki parol noto'g'ri")
        if not user.is_active:
            raise serializers.ValidationError("Foydalanuvchi bloklangan")

        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'phone_number': user.phone_number,
                'role': user.role,
            },
        }
