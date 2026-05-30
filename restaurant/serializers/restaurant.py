from rest_framework import serializers

from restaurant.models import Restaurants, RestaurantSettings


class RestaurantSettingsSerializer(serializers.ModelSerializer):
    currency_name = serializers.CharField(source='currency.name', read_only=True)

    class Meta:
        model = RestaurantSettings
        fields = ('id', 'currency', 'currency_name', 'service_fee',
                  'notify_orders', 'notify_staff', 'notify_daily')


class RestaurantSettingsUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantSettings
        fields = ('currency', 'service_fee', 'notify_orders', 'notify_staff', 'notify_daily')


class RestaurantListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurants
        fields = ('id', 'name', 'phone', 'created')


class RestaurantDetailSerializer(serializers.ModelSerializer):
    settings = RestaurantSettingsSerializer(source='restaurant_settings', many=True, read_only=True)

    class Meta:
        model = Restaurants
        fields = ('id', 'name', 'phone', 'created', 'settings')


class RestaurantCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurants
        fields = ('id', 'name', 'phone')


class RestaurantUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurants
        fields = ('name', 'phone')
