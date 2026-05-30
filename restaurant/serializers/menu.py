from rest_framework import serializers

from restaurant.models import MenuCategory, MenuItems


class MenuCategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = ('id', 'name', 'icon', 'restaurant', 'created')


class MenuCategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = ('id', 'name', 'icon', 'restaurant')


class MenuCategoryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = ('name', 'icon')


class MenuItemListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = MenuItems
        fields = ('id', 'name', 'price', 'category', 'category_name', 'restaurant', 'created')


class MenuItemDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = MenuItems
        fields = ('id', 'name', 'price', 'category', 'category_name', 'restaurant', 'created')


class MenuItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItems
        fields = ('id', 'name', 'price', 'category', 'restaurant')


class MenuItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItems
        fields = ('name', 'price', 'category')
