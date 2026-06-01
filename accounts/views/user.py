from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from drf_spectacular.utils import extend_schema_view, extend_schema

from accounts.models import Account, UserRoleChoices
from accounts.serializers.user import (
    UserListSerializer, UserDetailSerializer,
    UserCreateSerializer, UserUpdateSerializer,
)
from helpers.base_mixin import BaseViewSetMixin
from helpers.permissions import IsManagerOrAdmin


@extend_schema_view(
    list=extend_schema(tags=['Users'], summary="Xodimlar ro'yxati",
                       description="Restoran xodimlari ro'yxatini qaytaradi (ism, telefon, rol, qo'shilgan sana). Ism yoki telefon bo'yicha qidirish mumkin."),
    retrieve=extend_schema(tags=['Users'], summary="Xodim ma'lumoti",
                           description="Bitta xodimning to'liq ma'lumotini qaytaradi."),
    create=extend_schema(tags=['Users'], summary="Yangi xodim qo'shish",
                         description="Yangi xodim yaratadi (full_name, telefon, rol, parol). Faqat menejer yoki admin."),
    update=extend_schema(tags=['Users'], summary="Xodimni to'liq yangilash",
                         description="Xodim ma'lumotlarini to'liq yangilaydi. Faqat menejer yoki admin."),
    partial_update=extend_schema(tags=['Users'], summary="Xodimni qisman yangilash",
                                 description="Xodimning ayrim maydonlarini yangilaydi. Faqat menejer yoki admin."),
    destroy=extend_schema(tags=['Users'], summary="Xodimni o'chirish",
                          description="Xodimni soft-delete qiladi (deleted_at belgilanadi). Faqat menejer yoki admin."),
)
class UserViewSet(BaseViewSetMixin, ModelViewSet):
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['username', 'phone_number']
    ordering_fields = ['created_at', 'username']
    ordering = ['-created_at']

    action_serializer_class = {
        'list': UserListSerializer,
        'retrieve': UserDetailSerializer,
        'create': UserCreateSerializer,
        'update': UserUpdateSerializer,
        'partial_update': UserUpdateSerializer,
    }

    action_permission_classes = {
        'create': [IsAuthenticated, IsManagerOrAdmin],
        'update': [IsAuthenticated, IsManagerOrAdmin],
        'partial_update': [IsAuthenticated, IsManagerOrAdmin],
        'destroy': [IsAuthenticated, IsManagerOrAdmin],
    }

    def get_queryset(self):
        user = self.request.user
        qs = Account.objects.filter(deleted_at__isnull=True)
        if user.restaurant:
            qs = qs.filter(restaurant=user.restaurant)
        return qs

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()

    @extend_schema(tags=['Users'], summary="Xodim lavozimlari ro'yxati",
                   description="Tizimda mavjud bo'lgan xodim lavozimlarini (rollarni) qaytaradi.")
    @action(detail=False, methods=['get'], url_path='roles')
    def roles(self, request):
        data = [{'value': value, 'label': label} for value, label in UserRoleChoices.choices]
        return Response(data)
