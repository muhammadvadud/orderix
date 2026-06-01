from rest_framework import serializers
from django.db import transaction

from order.models import Order, OrderItems, OrderStatusChoices, OrderItemStatusChoices
from restaurant.models import MenuItems, Locations, RestaurantSettings


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)

    class Meta:
        model = OrderItems
        fields = ('id', 'menu_item', 'menu_item_name', 'quantity', 'price', 'subtotal', 'status')
        read_only_fields = ('price', 'subtotal')


class OrderItemCreateSerializer(serializers.Serializer):
    menu_item_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_menu_item_id(self, value):
        if not MenuItems.objects.filter(pk=value, deleted_at__isnull=True).exists():
            raise serializers.ValidationError("Taom topilmadi")
        return value


class OrderItemStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=OrderItemStatusChoices.choices)


class OrderItemQuantityUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class OrderItemsBulkSerializer(serializers.Serializer):
    items = OrderItemCreateSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Kamida bitta taom bo'lishi kerak")
        return value


class OrderListSerializer(serializers.ModelSerializer):
    waiter_name = serializers.SerializerMethodField()
    location_name = serializers.CharField(source='location.name', read_only=True)
    # get_queryset'da annotate qilingan: taomlar umumiy soni va qatorlar soni
    items_count = serializers.IntegerField(read_only=True)
    items_lines = serializers.IntegerField(read_only=True)

    def get_waiter_name(self, obj) -> str:
        return obj.waiter.full_name or obj.waiter.username

    class Meta:
        model = Order
        fields = ('id', 'waiter', 'waiter_name', 'location', 'location_name',
                  'status', 'total_amount', 'service_fee', 'items_count', 'items_lines', 'created', 'closed')
        read_only_fields = ('waiter', 'total_amount', 'service_fee', 'closed')


class OrderDetailSerializer(serializers.ModelSerializer):
    waiter_name = serializers.SerializerMethodField()
    location_name = serializers.CharField(source='location.name', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    def get_waiter_name(self, obj) -> str:
        return obj.waiter.full_name or obj.waiter.username

    class Meta:
        model = Order
        fields = ('id', 'waiter', 'waiter_name', 'location', 'location_name',
                  'status', 'total_amount', 'service_fee', 'items', 'created', 'closed')
        read_only_fields = ('waiter', 'total_amount', 'service_fee', 'closed')


class OrderCreateSerializer(serializers.Serializer):
    location_id = serializers.IntegerField()
    items = OrderItemCreateSerializer(many=True)

    def validate_location_id(self, value):
        user = self.context['request'].user
        if not Locations.objects.filter(pk=value, restaurant=user.restaurant).exists():
            raise serializers.ValidationError("Lokatsiya topilmadi")

        if Order.objects.filter(
            location_id=value,
            status__in=[OrderStatusChoices.PREPARING, OrderStatusChoices.DELIVERED]
        ).exists():
            raise serializers.ValidationError("Bu lokatsiyada allaqachon aktiv buyurtma mavjud")
        return value

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Kamida bitta taom bo'lishi kerak")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        items_data = validated_data['items']

        with transaction.atomic():
            settings = RestaurantSettings.objects.filter(restaurant=user.restaurant).first()
            service_fee_pct = settings.service_fee if settings else 0

            subtotal = 0
            order_items = []
            for item_data in items_data:
                menu_item = MenuItems.objects.get(pk=item_data['menu_item_id'])
                quantity = item_data['quantity']
                item_subtotal = menu_item.price * quantity
                subtotal += item_subtotal
                order_items.append({
                    'menu_item': menu_item,
                    'quantity': quantity,
                    'price': menu_item.price,
                    'subtotal': item_subtotal,
                })

            total_amount = subtotal + (subtotal * service_fee_pct / 100)

            order = Order.objects.create(
                waiter=user,
                restaurant=user.restaurant,
                location_id=validated_data['location_id'],
                total_amount=total_amount,
                service_fee=service_fee_pct,
            )

            for item in order_items:
                OrderItems.objects.create(
                    order=order,
                    menu_item=item['menu_item'],
                    quantity=item['quantity'],
                    price=item['price'],
                    subtotal=item['subtotal'],
                )

        return order


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=OrderStatusChoices.choices)

    VALID_TRANSITIONS = {
        OrderStatusChoices.PREPARING: [OrderStatusChoices.DELIVERED, OrderStatusChoices.CANCELLED],
        OrderStatusChoices.DELIVERED: [OrderStatusChoices.CLOSED, OrderStatusChoices.CANCELLED],
        OrderStatusChoices.CLOSED: [],
        OrderStatusChoices.CANCELLED: [],
    }

    def validate(self, attrs):
        new_status = attrs['status']
        current_status = self.instance.status
        if new_status not in self.VALID_TRANSITIONS.get(current_status, []):
            raise serializers.ValidationError(
                f"'{current_status}' dan '{new_status}' ga o'tish mumkin emas"
            )
        return attrs
