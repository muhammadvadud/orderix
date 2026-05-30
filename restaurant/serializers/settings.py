from rest_framework import serializers

from restaurant.models import Currency


class SettingsSerializer(serializers.Serializer):
    """Restoran umumiy sozlamalari (GET javobi va PATCH uchun)."""
    restaurant_name = serializers.CharField(required=False)
    restaurant_phone = serializers.CharField(required=False, allow_blank=True)
    currency = serializers.PrimaryKeyRelatedField(
        queryset=Currency.objects.all(), required=False)
    currency_name = serializers.CharField(read_only=True)
    service_fee = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False)
    notify_orders = serializers.BooleanField(required=False)
    notify_staff = serializers.BooleanField(required=False)
    notify_daily = serializers.BooleanField(required=False)
