from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

from restaurant.models import Restaurants, RestaurantSettings
from restaurant.serializers.restaurant import (
    RestaurantListSerializer, RestaurantDetailSerializer,
    RestaurantCreateSerializer, RestaurantUpdateSerializer,
    RestaurantSettingsSerializer, RestaurantSettingsUpdateSerializer,
)
from helpers.base_mixin import BaseViewSetMixin
from helpers.permissions import IsManagerOrAdmin, IsAdmin


class RestaurantViewSet(BaseViewSetMixin, ModelViewSet):
    serializer_class = RestaurantListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'phone']
    ordering_fields = ['name', 'created']
    ordering = ['-created']

    action_serializer_class = {
        'list': RestaurantListSerializer,
        'retrieve': RestaurantDetailSerializer,
        'create': RestaurantCreateSerializer,
        'update': RestaurantUpdateSerializer,
        'partial_update': RestaurantUpdateSerializer,
    }

    action_permission_classes = {
        'create': [IsAuthenticated, IsAdmin],
        'destroy': [IsAuthenticated, IsAdmin],
    }

    def get_queryset(self):
        return Restaurants.objects.filter(deleted_at__isnull=True)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=True, methods=['get', 'put', 'patch'], url_path='settings',
            permission_classes=[IsAuthenticated, IsManagerOrAdmin])
    def restaurant_settings(self, request, pk=None):
        restaurant = self.get_object()

        if request.method == 'GET':
            obj = RestaurantSettings.objects.filter(restaurant=restaurant).first()
            if not obj:
                return Response({})
            return Response(RestaurantSettingsSerializer(obj).data)

        obj = RestaurantSettings.objects.filter(restaurant=restaurant).first()
        serializer = RestaurantSettingsUpdateSerializer(
            obj, data=request.data, partial=(request.method == 'PATCH')
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(restaurant=restaurant)
        return Response(RestaurantSettingsSerializer(instance).data)
