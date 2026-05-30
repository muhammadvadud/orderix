from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema

from restaurant.models import RestaurantSettings
from restaurant.serializers.settings import SettingsSerializer
from helpers.permissions import IsManagerOrAdmin


def _build_settings_data(restaurant):
    settings = RestaurantSettings.objects.filter(restaurant=restaurant).select_related('currency').first()
    return {
        'restaurant_name': restaurant.name,
        'restaurant_phone': restaurant.phone,
        'currency': settings.currency_id if settings else None,
        'currency_name': settings.currency.name if settings else None,
        'service_fee': settings.service_fee if settings else None,
        'notify_orders': settings.notify_orders if settings else True,
        'notify_staff': settings.notify_staff if settings else False,
        'notify_daily': settings.notify_daily if settings else True,
    }


@extend_schema(tags=['Settings'])
class SettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'PATCH':
            return [IsAuthenticated(), IsManagerOrAdmin()]
        return [IsAuthenticated()]

    @extend_schema(summary="Sozlamalarni olish", responses=SettingsSerializer,
                   description="Joriy restoranning sozlamalarini qaytaradi: nomi, telefoni, valyutasi, "
                               "xizmat haqi (service_fee) va bildirishnoma sozlamalari.")
    def get(self, request):
        return Response({
            'status': True,
            'message': 'OK',
            'data': _build_settings_data(request.user.restaurant),
        })

    @extend_schema(summary="Sozlamalarni yangilash", request=SettingsSerializer,
                   responses=SettingsSerializer,
                   description="Restoran nomi, valyuta, xizmat haqi va bildirishnoma sozlamalarini yangilaydi. "
                               "Faqat menejer yoki admin.")
    def patch(self, request):
        restaurant = request.user.restaurant
        serializer = SettingsSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if 'restaurant_name' in data:
            restaurant.name = data['restaurant_name']
        if 'restaurant_phone' in data:
            restaurant.phone = data['restaurant_phone']
        restaurant.save()

        settings = RestaurantSettings.objects.filter(restaurant=restaurant).first()
        if not settings:
            if 'currency' not in data or 'service_fee' not in data:
                raise ValidationError("Sozlama birinchi marta yaratilayotganda valyuta va xizmat haqi kerak")
            settings = RestaurantSettings(restaurant=restaurant)

        for field in ('currency', 'service_fee', 'notify_orders', 'notify_staff', 'notify_daily'):
            if field in data:
                setattr(settings, field, data[field])
        settings.save()

        return Response({
            'status': True,
            'message': 'Sozlamalar yangilandi',
            'data': _build_settings_data(restaurant),
        })
