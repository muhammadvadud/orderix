from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from drf_spectacular.utils import extend_schema_view, extend_schema

from restaurant.models import MenuCategory, MenuItems
from restaurant.serializers.menu import (
    MenuCategoryListSerializer, MenuCategoryCreateSerializer, MenuCategoryUpdateSerializer,
    MenuItemListSerializer, MenuItemDetailSerializer,
    MenuItemCreateSerializer, MenuItemUpdateSerializer,
)
from helpers.base_mixin import BaseViewSetMixin
from helpers.permissions import IsManagerOrAdmin


@extend_schema_view(
    list=extend_schema(tags=['Menu'], summary="Kategoriyalar ro'yxati",
                       description="Menu kategoriyalari ro'yxati (nomi va icon)."),
    retrieve=extend_schema(tags=['Menu'], summary="Kategoriya ma'lumoti",
                           description="Bitta menu kategoriyasini qaytaradi."),
    create=extend_schema(tags=['Menu'], summary="Kategoriya qo'shish",
                         description="Yangi menu kategoriyasi yaratadi (nomi + icon). Faqat menejer yoki admin."),
    update=extend_schema(tags=['Menu'], summary="Kategoriyani yangilash",
                         description="Kategoriya nomi va iconini to'liq yangilaydi. Faqat menejer yoki admin."),
    partial_update=extend_schema(tags=['Menu'], summary="Kategoriyani qisman yangilash",
                                 description="Kategoriyaning ayrim maydonlarini yangilaydi. Faqat menejer yoki admin."),
    destroy=extend_schema(tags=['Menu'], summary="Kategoriyani o'chirish",
                          description="Menu kategoriyasini o'chiradi. Faqat menejer yoki admin."),
)
class MenuCategoryViewSet(BaseViewSetMixin, ModelViewSet):
    serializer_class = MenuCategoryListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created']
    ordering = ['name']

    action_serializer_class = {
        'list': MenuCategoryListSerializer,
        'retrieve': MenuCategoryListSerializer,
        'create': MenuCategoryCreateSerializer,
        'update': MenuCategoryUpdateSerializer,
        'partial_update': MenuCategoryUpdateSerializer,
    }

    action_permission_classes = {
        'create': [IsAuthenticated, IsManagerOrAdmin],
        'update': [IsAuthenticated, IsManagerOrAdmin],
        'partial_update': [IsAuthenticated, IsManagerOrAdmin],
        'destroy': [IsAuthenticated, IsManagerOrAdmin],
    }

    def get_queryset(self):
        return MenuCategory.objects.filter(restaurant=self.request.user.restaurant)


@extend_schema_view(
    list=extend_schema(tags=['Menu'], summary="Taomlar ro'yxati",
                       description="Menu taomlari ro'yxati (nomi, narx, kategoriya). Nomi bo'yicha qidirish mumkin."),
    retrieve=extend_schema(tags=['Menu'], summary="Taom ma'lumoti",
                           description="Bitta taomning to'liq ma'lumotini qaytaradi."),
    create=extend_schema(tags=['Menu'], summary="Taom qo'shish",
                         description="Yangi taom yaratadi (nomi, narx, kategoriya). Faqat menejer yoki admin."),
    update=extend_schema(tags=['Menu'], summary="Taomni yangilash",
                         description="Taom ma'lumotlarini to'liq yangilaydi. Faqat menejer yoki admin."),
    partial_update=extend_schema(tags=['Menu'], summary="Taomni qisman yangilash",
                                 description="Taomning ayrim maydonlarini yangilaydi. Faqat menejer yoki admin."),
    destroy=extend_schema(tags=['Menu'], summary="Taomni o'chirish",
                          description="Taomni soft-delete qiladi. Faqat menejer yoki admin."),
)
class MenuItemViewSet(BaseViewSetMixin, ModelViewSet):
    serializer_class = MenuItemListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'price', 'created']
    ordering = ['name']

    action_serializer_class = {
        'list': MenuItemListSerializer,
        'retrieve': MenuItemDetailSerializer,
        'create': MenuItemCreateSerializer,
        'update': MenuItemUpdateSerializer,
        'partial_update': MenuItemUpdateSerializer,
    }

    action_permission_classes = {
        'create': [IsAuthenticated, IsManagerOrAdmin],
        'update': [IsAuthenticated, IsManagerOrAdmin],
        'partial_update': [IsAuthenticated, IsManagerOrAdmin],
        'destroy': [IsAuthenticated, IsManagerOrAdmin],
    }

    def get_queryset(self):
        return MenuItems.objects.filter(
            restaurant=self.request.user.restaurant,
            deleted_at__isnull=True,
        )

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()
