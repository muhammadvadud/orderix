from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter

from restaurant.models import Locations
from restaurant.serializers.location import (
    LocationListSerializer, LocationDetailSerializer,
    LocationCreateSerializer, LocationUpdateSerializer,
)
from helpers.base_mixin import BaseViewSetMixin
from helpers.permissions import IsManagerOrAdmin


class LocationViewSet(BaseViewSetMixin, ModelViewSet):
    serializer_class = LocationListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created']
    ordering = ['name']

    action_serializer_class = {
        'list': LocationListSerializer,
        'retrieve': LocationDetailSerializer,
        'create': LocationCreateSerializer,
        'update': LocationUpdateSerializer,
        'partial_update': LocationUpdateSerializer,
    }

    action_permission_classes = {
        'create': [IsAuthenticated, IsManagerOrAdmin],
        'update': [IsAuthenticated, IsManagerOrAdmin],
        'partial_update': [IsAuthenticated, IsManagerOrAdmin],
        'destroy': [IsAuthenticated, IsManagerOrAdmin],
    }

    def get_queryset(self):
        user = self.request.user
        qs = Locations.objects.filter(restaurant=user.restaurant)
        if self.action == 'list':
            qs = qs.filter(parent__isnull=True)
        return qs

    def perform_destroy(self, instance):
        if instance.children.exists():
            raise ValidationError("Farzandlari mavjud bo'lgan lokatsiyani o'chirib bo'lmaydi")
        instance.delete()
