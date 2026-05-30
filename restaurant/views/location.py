from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter

from restaurant.models import Locations, LocationTypeChoices
from restaurant.serializers.location import (
    LocationListSerializer, LocationDetailSerializer,
    LocationCreateSerializer, LocationUpdateSerializer,
    ZoneWithTablesSerializer, TableStatusSerializer,
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
    zones=extend_schema(tags=['Locations'], summary="Zonalar (stollari bilan)",
                        description="Barcha zonalarni ichidagi stollari bilan birga (nested) qaytaradi. "
                                    "Ofitsiant ilovasidagi stollar ekrani uchun qulay.",
                        responses=ZoneWithTablesSerializer(many=True)),
    set_status=extend_schema(tags=['Locations'], summary="Stol statusini o'zgartirish",
                             description="Stol statusini qo'lda o'zgartiradi (free/reserved/dirty). "
                                         "occupied statusi aktiv buyurtmadan avtomatik hisoblanadi va qo'lda o'rnatilmaydi.",
                             request=TableStatusSerializer),
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
            type_param = self.request.query_params.get('type')
            parent_param = self.request.query_params.get('parent')
            if type_param:
                qs = qs.filter(type=type_param)
            elif not parent_param:
                # standart: faqat zonalar
                qs = qs.filter(type=LocationTypeChoices.ZONE)
            if parent_param:
                qs = qs.filter(parent_id=parent_param)
        return qs

    def perform_destroy(self, instance):
        if instance.children.exists():
            raise ValidationError("Farzandlari mavjud bo'lgan lokatsiyani o'chirib bo'lmaydi")
        instance.delete()

    @action(detail=False, methods=['get'], url_path='zones')
    def zones(self, request):
        zones = Locations.objects.filter(
            restaurant=request.user.restaurant,
            type=LocationTypeChoices.ZONE,
        ).order_by('name')
        serializer = ZoneWithTablesSerializer(zones, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='status',
            permission_classes=[IsAuthenticated])
    def set_status(self, request, pk=None):
        table = self.get_object()
        if table.type != LocationTypeChoices.TABLE:
            raise ValidationError("Status faqat stol uchun o'zgartiriladi")

        serializer = TableStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        table.status = serializer.validated_data['status']
        table.save(update_fields=['status'])
        return Response(LocationDetailSerializer(table).data)
