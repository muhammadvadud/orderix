from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import (
    TokenRefreshView as BaseTokenRefreshView,
    TokenVerifyView as BaseTokenVerifyView,
)

from accounts.serializers.auth import LoginSerializer
from accounts.serializers.user import UserDetailSerializer


@extend_schema(tags=['Auth'], summary="Login (telefon + parol)",
               description="Telefon raqam va parol orqali tizimga kirish. access va refresh token hamda foydalanuvchi ma'lumotini qaytaradi.",
               request=LoginSerializer, responses=LoginSerializer)
class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = 'login'

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({
            'status': True,
            'message': 'OK',
            'data': serializer.validated_data,
        })


@extend_schema(tags=['Auth'], summary="Tokenni yangilash",
               description="refresh token orqali yangi access token oladi.")
class TokenRefreshView(BaseTokenRefreshView):
    pass


@extend_schema(tags=['Auth'], summary="Tokenni tekshirish",
               description="Berilgan token amal qilishini tekshiradi.")
class TokenVerifyView(BaseTokenVerifyView):
    pass


@extend_schema(tags=['Auth'], summary="Joriy foydalanuvchi",
               description="Token egasi bo'lgan foydalanuvchining profil ma'lumotini qaytaradi.",
               responses=UserDetailSerializer)
class GetMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response({
            'status': True,
            'message': 'OK',
            'data': serializer.data,
        })
