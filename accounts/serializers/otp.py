import random

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta

from accounts.models import Account, OtpCode

OTP_TTL_MINUTES = 5


class OtpRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def validate_phone_number(self, value):
        if not Account.objects.filter(phone_number=value, deleted_at__isnull=True).exists():
            raise serializers.ValidationError("Bu raqam bilan foydalanuvchi topilmadi")
        return value

    def create(self, validated_data):
        phone_number = validated_data['phone_number']
        code = f'{random.randint(0, 999999):06d}'
        # eski yuborilgan kodlarni ishlatilgan deb belgilaymiz
        OtpCode.objects.filter(phone_number=phone_number, is_used=False).update(is_used=True)
        otp = OtpCode.objects.create(
            phone_number=phone_number,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=OTP_TTL_MINUTES),
        )
        # TODO: kod @OrderiX_AuthBot orqali Telegram'ga yuboriladi.
        # Demo bosqichida kod response'da qaytariladi.
        return otp


class OtpVerifySerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        otp = OtpCode.objects.filter(
            phone_number=attrs['phone_number'],
            code=attrs['code'],
            is_used=False,
        ).order_by('-created_at').first()

        if not otp:
            raise serializers.ValidationError("Kod noto'g'ri")
        if otp.expires_at < timezone.now():
            raise serializers.ValidationError("Kod muddati tugagan")

        user = Account.objects.filter(
            phone_number=attrs['phone_number'], deleted_at__isnull=True
        ).first()
        if not user:
            raise serializers.ValidationError("Foydalanuvchi topilmadi")
        if not user.is_active:
            raise serializers.ValidationError("Foydalanuvchi bloklangan")

        otp.is_used = True
        otp.save(update_fields=['is_used'])

        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'phone_number': user.phone_number,
                'role': user.role,
            },
        }
