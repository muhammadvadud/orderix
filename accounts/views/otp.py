from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from drf_spectacular.utils import extend_schema

from accounts.serializers.otp import OtpRequestSerializer, OtpVerifySerializer


@extend_schema(tags=['Auth'], summary="Telegram OTP so'rash",
               description="Telefon raqamga 6 xonali tasdiqlash kodini yuboradi (@OrderiX_AuthBot orqali). "
                           "Demo rejimida kod javobda `code` maydonida qaytariladi.",
               request=OtpRequestSerializer, responses=OtpRequestSerializer)
class OtpRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = 'otp_request'

    def post(self, request):
        serializer = OtpRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        data = {'phone_number': result['phone_number'], 'expires_at': result['expires_at']}
        # Demo: bot integratsiyasi tayyor bo'lmaguncha kodni qaytaramiz
        if settings.DEBUG and result.get('code'):
            data['code'] = result['code']

        return Response({
            'status': True,
            'message': 'Tasdiqlash kodi yuborildi',
            'data': data,
        })


@extend_schema(tags=['Auth'], summary="Telegram OTP tasdiqlash",
               description="Telefon raqam va kodni tekshiradi. To'g'ri bo'lsa access/refresh token va "
                           "foydalanuvchi ma'lumotini qaytaradi.",
               request=OtpVerifySerializer, responses=OtpVerifySerializer)
class OtpVerifyView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = 'otp_verify'

    def post(self, request):
        serializer = OtpVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({
            'status': True,
            'message': 'OK',
            'data': serializer.validated_data,
        })
