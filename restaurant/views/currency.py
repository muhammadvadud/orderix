from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema_view, extend_schema

from restaurant.models import Currency
from restaurant.serializers.currency import CurrencySerializer, CurrencyCreateSerializer
from helpers.base_mixin import BaseViewSetMixin
from helpers.permissions import IsManagerOrAdmin


@extend_schema_view(
    list=extend_schema(tags=['Currencies']),
    retrieve=extend_schema(tags=['Currencies']),
    create=extend_schema(tags=['Currencies']),
)
class CurrencyViewSet(BaseViewSetMixin, ModelViewSet):
    serializer_class = CurrencySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    action_serializer_class = {
        'list': CurrencySerializer,
        'retrieve': CurrencySerializer,
        'create': CurrencyCreateSerializer,
    }

    action_permission_classes = {
        'create': [IsAuthenticated, IsManagerOrAdmin],
    }

    def get_queryset(self):
        return Currency.objects.all()
