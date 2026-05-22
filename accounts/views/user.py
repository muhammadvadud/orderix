from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from drf_spectacular.utils import extend_schema_view, extend_schema

from accounts.models import Account
from accounts.serializers.user import (
    UserListSerializer, UserDetailSerializer,
    UserCreateSerializer, UserUpdateSerializer,
)
from helpers.base_mixin import BaseViewSetMixin
from helpers.permissions import IsManagerOrAdmin


@extend_schema_view(
    list=extend_schema(tags=['Users']),
    retrieve=extend_schema(tags=['Users']),
    create=extend_schema(tags=['Users']),
    update=extend_schema(tags=['Users']),
    partial_update=extend_schema(tags=['Users']),
    destroy=extend_schema(tags=['Users']),
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
