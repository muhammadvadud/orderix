import secrets

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta

from accounts.models import Account, OtpCode

OTP_TTL_MINUTES = 5
OTP_MAX_ATTEMPTS = 5


class OtpRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def create(self, validated_data):
        phone_number = validated_data['phone_number']
        expires_at = timezone.now() + timedelta(minutes=OTP_TTL_MINUTES)

        # Foydalanuvchi mavjudligini oshkor qilmaymiz (enumeration oldini olish):
        # raqam ro'yxatdan o'tmagan bo'lsa ham javob bir xil bo'ladi, faqat
        # kod yuborilmaydi.
        user_exists = Account.objects.filter(
            phone_number=phone_number, deleted_at__isnull=True
        ).exists()
        if not user_exists:
            return {'phone_number': phone_number, 'expires_at': expires_at, 'code': None}

        # Xavfsiz tasodifiy 6 xonali kod (random emas, secrets)
        code = f'{secrets.randbelow(1000000):06d}'
        # eski yuborilgan kodlarni ishlatilgan deb belgilaymiz
        OtpCode.objects.filter(phone_number=phone_number, is_used=False).update(is_used=True)
        otp = OtpCode.objects.create(
            phone_number=phone_number,
            code=code,
            expires_at=expires_at,
        )
        # TODO: kod @OrderiX_AuthBot orqali Telegram'ga yuboriladi.
        # Demo bosqichida kod response'da qaytariladi.
        return {'phone_number': otp.phone_number, 'expires_at': otp.expires_at, 'code': otp.code}


class OtpVerifySerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        # Raqam bo'yicha eng oxirgi ishlatilmagan kodni olamiz (kod bo'yicha emas) —
        # shunda xato urinishlarni sanab, brute-force'ni cheklay olamiz.
        otp = OtpCode.objects.filter(
            phone_number=attrs['phone_number'],
            is_used=False,
        ).order_by('-created_at').first()

        if not otp or otp.expires_at < timezone.now():
            raise serializers.ValidationError("Kod noto'g'ri yoki muddati tugagan")

        if otp.attempts >= OTP_MAX_ATTEMPTS:
            otp.is_used = True
            otp.save(update_fields=['is_used'])
            raise serializers.ValidationError("Urinishlar soni tugadi, yangi kod so'rang")

        if not secrets.compare_digest(otp.code, attrs['code']):
            otp.attempts += 1
            if otp.attempts >= OTP_MAX_ATTEMPTS:
                otp.is_used = True
            otp.save(update_fields=['attempts', 'is_used'])
            raise serializers.ValidationError("Kod noto'g'ri")

        user = Account.objects.filter(
            phone_number=attrs['phone_number'], deleted_at__isnull=True
        ).first()
        if not user or not user.is_active:
            raise serializers.ValidationError("Kod noto'g'ri yoki muddati tugagan")

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
