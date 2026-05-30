from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from drf_spectacular.utils import extend_schema_view, extend_schema

from order.models import Order, OrderItems, OrderStatusChoices
from order.serializers.order import (
    OrderListSerializer, OrderDetailSerializer,
    OrderCreateSerializer, OrderStatusUpdateSerializer,
    OrderItemCreateSerializer,
)
from helpers.base_mixin import BaseViewSetMixin
from helpers.permissions import IsManagerOrAdmin


@extend_schema_view(
    list=extend_schema(tags=['Orders']),
    retrieve=extend_schema(tags=['Orders']),
    create=extend_schema(tags=['Orders']),
    partial_update=extend_schema(tags=['Orders']),
    destroy=extend_schema(tags=['Orders']),
    update_status=extend_schema(tags=['Orders']),
    add_item=extend_schema(tags=['Orders']),
    remove_item=extend_schema(tags=['Orders']),
)
class OrderViewSet(BaseViewSetMixin, ModelViewSet):
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['location__name', 'waiter__username']
    ordering_fields = ['created', 'total_amount', 'status']
    ordering = ['-created']

    action_serializer_class = {
        'list': OrderListSerializer,
        'retrieve': OrderDetailSerializer,
    }

    action_permission_classes = {
        'destroy': [IsAuthenticated, IsManagerOrAdmin],
    }

    def get_queryset(self):
        user = self.request.user
        qs = Order.objects.filter(restaurant=user.restaurant).select_related('waiter', 'location')
        if user.role == 'waiter':
            qs = qs.filter(waiter=user)

        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)

        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            qs = qs.filter(created__date__gte=date_from)
        if date_to:
            qs = qs.filter(created__date__lte=date_to)

        return qs.order_by('-created')

    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderDetailSerializer(order).data, status=201)

    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(order, data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        order.status = new_status
        if new_status in (OrderStatusChoices.CLOSED, OrderStatusChoices.CANCELLED):
            order.closed = timezone.now()
        order.save()

        return Response(OrderDetailSerializer(order).data)

    @action(detail=True, methods=['post'], url_path='items')
    def add_item(self, request, pk=None):
        order = self.get_object()
        if order.status not in (OrderStatusChoices.PREPARING, OrderStatusChoices.DELIVERED):
            raise ValidationError("Yopilgan buyurtmaga taom qo'shib bo'lmaydi")

        serializer = OrderItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from restaurant.models import MenuItems
        menu_item = MenuItems.objects.get(pk=serializer.validated_data['menu_item_id'])
        quantity = serializer.validated_data['quantity']
        price = menu_item.price
        subtotal = price * quantity

        OrderItems.objects.create(
            order=order,
            menu_item=menu_item,
            quantity=quantity,
            price=price,
            subtotal=subtotal,
        )
        self._recalculate_total(order)

        return Response(OrderDetailSerializer(order).data)

    @action(detail=True, methods=['delete'], url_path=r'items/(?P<item_id>[^/.]+)')
    def remove_item(self, request, pk=None, item_id=None):
        order = self.get_object()
        if order.status not in (OrderStatusChoices.PREPARING, OrderStatusChoices.DELIVERED):
            raise ValidationError("Yopilgan buyurtmadan taom o'chirib bo'lmaydi")

        try:
            item = OrderItems.objects.get(pk=item_id, order=order)
        except OrderItems.DoesNotExist:
            raise NotFound("Buyurtma elementi topilmadi")

        item.delete()
        self._recalculate_total(order)

        return Response(OrderDetailSerializer(order).data)

    def _recalculate_total(self, order):
        from restaurant.models import RestaurantSettings
        settings = RestaurantSettings.objects.filter(restaurant=order.restaurant).first()
        service_fee_pct = settings.service_fee if settings else 0

        subtotal = sum(item.price * item.quantity for item in order.items.all())
        order.total_amount = subtotal + (subtotal * service_fee_pct / 100)
        order.save(update_fields=['total_amount'])
