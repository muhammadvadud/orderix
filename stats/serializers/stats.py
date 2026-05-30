from rest_framework import serializers


class TrendSerializer(serializers.Serializer):
    orders = serializers.FloatField(help_text="Buyurtmalar o'zgarishi (%, kechagi kunga nisbatan)")
    revenue = serializers.FloatField(help_text="Tushum o'zgarishi (%, kechagi kunga nisbatan)")


class RecentOrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    waiter_name = serializers.CharField()
    location_name = serializers.CharField()
    status = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    created = serializers.DateTimeField()


class DashboardSerializer(serializers.Serializer):
    orders_today = serializers.IntegerField()
    revenue_today = serializers.DecimalField(max_digits=15, decimal_places=2)
    active_waiters = serializers.IntegerField()
    open_orders = serializers.IntegerField()
    trends = TrendSerializer()
    recent_orders = RecentOrderSerializer(many=True)


class TopItemSerializer(serializers.Serializer):
    menu_id = serializers.IntegerField()
    name = serializers.CharField()
    qty = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=15, decimal_places=2)


class SeriesPointSerializer(serializers.Serializer):
    day = serializers.CharField(help_text="Hafta kuni qisqa nomi (Mon, Tue, ...)")
    date = serializers.DateField()
    revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    orders = serializers.IntegerField()


class WaiterStatsSerializer(serializers.Serializer):
    orders_today = serializers.IntegerField()
    revenue_today = serializers.DecimalField(max_digits=15, decimal_places=2)
    orders_week = serializers.IntegerField()
    revenue_week = serializers.DecimalField(max_digits=15, decimal_places=2)
    active_orders = serializers.IntegerField()
    total_orders = serializers.IntegerField()
