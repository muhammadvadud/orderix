from rest_framework import serializers

from restaurant.models import Locations, LocationTypeChoices, TableStatusChoices
from order.models import OrderStatusChoices


def _is_table_occupied(table):
    """Stolda aktiv (preparing/delivered) buyurtma bo'lsa True."""
    return table.orders.filter(
        status__in=[OrderStatusChoices.PREPARING, OrderStatusChoices.DELIVERED]
    ).exists()


class TableSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Locations
        fields = ('id', 'name', 'number', 'seats', 'status', 'parent', 'created')

    def get_status(self, obj):
        # occupied bazada saqlanmaydi — aktiv buyurtmadan hisoblanadi
        if obj.status in (TableStatusChoices.RESERVED, TableStatusChoices.DIRTY):
            return obj.status
        return TableStatusChoices.OCCUPIED if _is_table_occupied(obj) else TableStatusChoices.FREE


class ZoneWithTablesSerializer(serializers.ModelSerializer):
    """Zona va uning stollari (frontend qulayligi uchun nested)."""
    tables = serializers.SerializerMethodField()

    class Meta:
        model = Locations
        fields = ('id', 'name', 'short', 'icon', 'color', 'tables', 'created')

    def get_tables(self, obj):
        tables = obj.children.filter(type=LocationTypeChoices.TABLE).order_by('number')
        return TableSerializer(tables, many=True).data


class LocationListSerializer(serializers.ModelSerializer):
    children = TableSerializer(many=True, read_only=True)

    class Meta:
        model = Locations
        fields = ('id', 'type', 'name', 'short', 'icon', 'color', 'number',
                  'seats', 'status', 'parent', 'children', 'created')


class LocationDetailSerializer(serializers.ModelSerializer):
    children = TableSerializer(many=True, read_only=True)

    class Meta:
        model = Locations
        fields = ('id', 'type', 'name', 'short', 'icon', 'color', 'number',
                  'seats', 'status', 'parent', 'restaurant', 'children', 'created')


class LocationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locations
        fields = ('id', 'type', 'name', 'short', 'icon', 'color', 'number',
                  'seats', 'status', 'parent', 'restaurant')


class LocationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locations
        fields = ('type', 'name', 'short', 'icon', 'color', 'number', 'seats', 'status', 'parent')


class TableStatusSerializer(serializers.Serializer):
    """Stol statusini qo'lda o'zgartirish (reserved/dirty/free)."""
    status = serializers.ChoiceField(choices=[
        TableStatusChoices.FREE,
        TableStatusChoices.RESERVED,
        TableStatusChoices.DIRTY,
    ])
