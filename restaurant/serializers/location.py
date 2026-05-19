from rest_framework import serializers

from restaurant.models import Locations


class LocationChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locations
        fields = ('id', 'name', 'created')


class LocationListSerializer(serializers.ModelSerializer):
    children = LocationChildSerializer(many=True, read_only=True)

    class Meta:
        model = Locations
        fields = ('id', 'name', 'parent', 'children', 'created')


class LocationDetailSerializer(serializers.ModelSerializer):
    children = LocationChildSerializer(many=True, read_only=True)

    class Meta:
        model = Locations
        fields = ('id', 'name', 'parent', 'restaurant', 'children', 'created')


class LocationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locations
        fields = ('id', 'name', 'parent', 'restaurant')


class LocationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locations
        fields = ('name', 'parent')
