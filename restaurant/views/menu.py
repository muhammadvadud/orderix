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
    list=extend_schema(tags=['Menu']),
    retrieve=extend_schema(tags=['Menu']),
    create=extend_schema(tags=['Menu']),
    update=extend_schema(tags=['Menu']),
    partial_update=extend_schema(tags=['Menu']),
    destroy=extend_schema(tags=['Menu']),
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
    list=extend_schema(tags=['Menu']),
    retrieve=extend_schema(tags=['Menu']),
    create=extend_schema(tags=['Menu']),
    update=extend_schema(tags=['Menu']),
    partial_update=extend_schema(tags=['Menu']),
    destroy=extend_schema(tags=['Menu']),
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
