from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema_view, extend_schema

from restaurant.models import Locations
from restaurant.serializers.location import (
    LocationListSerializer, LocationDetailSerializer,
    LocationCreateSerializer, LocationUpdateSerializer,
)
from helpers.base_mixin import BaseViewSetMixin
from helpers.permissions import IsManagerOrAdmin


@extend_schema_view(
    list=extend_schema(tags=['Locations'], summary="Lokatsiyalar ro'yxati",
                       description="Zona va stollar ro'yxati. `type=zone|table` va `parent=ID` query paramlari bilan filtrlash mumkin. type berilmasa faqat zonalar qaytadi."),
    retrieve=extend_schema(tags=['Locations'], summary="Lokatsiya ma'lumoti",
                           description="Bitta zona yoki stolni qaytaradi."),
    create=extend_schema(tags=['Locations'], summary="Lokatsiya qo'shish",
                         description="Yangi zona (type=zone) yoki stol (type=table, parent=zona) yaratadi. Faqat menejer yoki admin."),
    update=extend_schema(tags=['Locations'], summary="Lokatsiyani yangilash",
                         description="Zona yoki stol ma'lumotlarini to'liq yangilaydi. Faqat menejer yoki admin."),
    partial_update=extend_schema(tags=['Locations'], summary="Lokatsiyani qisman yangilash",
                                 description="Ayrim maydonlarni yangilaydi. Faqat menejer yoki admin."),
    destroy=extend_schema(tags=['Locations'], summary="Lokatsiyani o'chirish",
                          description="Zona yoki stolni o'chiradi. Farzandlari bor zonani o'chirib bo'lmaydi."),
)
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
