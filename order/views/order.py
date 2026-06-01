from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound, MethodNotAllowed
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction
from django.db.models import Sum, Count
from django.db.models.functions import Coalesce
from django.utils import timezone
from drf_spectacular.utils import extend_schema_view, extend_schema

from restaurant.models import MenuItems, RestaurantSettings

from order.models import Order, OrderItems, OrderStatusChoices, OrderItemStatusChoices
from order.serializers.order import (
    OrderListSerializer, OrderDetailSerializer,
    OrderCreateSerializer, OrderStatusUpdateSerializer,
    OrderItemCreateSerializer, OrderItemStatusUpdateSerializer,
    OrderItemQuantityUpdateSerializer, OrderItemsBulkSerializer,
)
from helpers.base_mixin import BaseViewSetMixin
from helpers.permissions import IsManagerOrAdmin


@extend_schema_view(
    list=extend_schema(tags=['Orders'], summary="Buyurtmalar ro'yxati",
                       description="Buyurtmalar ro'yxati. `status`, `date_from`, `date_to` query paramlari bilan filtrlash mumkin. Ofitsiant faqat o'z buyurtmalarini ko'radi."),
    retrieve=extend_schema(tags=['Orders'], summary="Buyurtma tafsiloti",
                           description="Bitta buyurtmani taomlari (items) bilan birga qaytaradi."),
    create=extend_schema(tags=['Orders'], summary="Buyurtma yaratish",
                         description="Yangi buyurtma yaratadi (location_id + items). Xizmat haqi (service_fee) avtomatik qo'shiladi. Bitta lokatsiyada faqat bitta aktiv buyurtma bo'lishi mumkin."),
    update=extend_schema(exclude=True),
    partial_update=extend_schema(tags=['Orders'], summary="Buyurtmani qisman yangilash",
                                 description="Buyurtmaning ayrim maydonlarini yangilaydi."),
    destroy=extend_schema(tags=['Orders'], summary="Buyurtmani o'chirish",
                          description="Buyurtmani o'chiradi. Faqat menejer yoki admin."),
    update_status=extend_schema(tags=['Orders'], summary="Buyurtma statusini o'zgartirish",
                                description="Buyurtma statusini o'zgartiradi (preparing → delivered → closed/cancelled). Status oqimi tekshiriladi."),
)
class OrderViewSet(BaseViewSetMixin, ModelViewSet):
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']
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
        qs = Order.objects.filter(restaurant=user.restaurant).select_related('waiter', 'location').annotate(
            items_count=Coalesce(Sum('items__quantity'), 0),
            items_lines=Count('items', distinct=True),
        )
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

    def update(self, request, *args, **kwargs):
        # Buyurtmani to'liq PUT bilan yangilash yopilgan — status va taomlar
        # alohida action'lar orqali boshqariladi. (PUT faqat /orders/{id}/items uchun)
        raise MethodNotAllowed('PUT')

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

    def _assert_editable(self, order, message):
        if order.status not in (OrderStatusChoices.PREPARING, OrderStatusChoices.DELIVERED):
            raise ValidationError(message)

    @extend_schema(methods=['POST'], tags=['Orders'], summary="Buyurtmaga taom qo'shish",
                   description="Aktiv buyurtmaga bitta taom qo'shadi va umumiy summani qayta hisoblaydi.",
                   request=OrderItemCreateSerializer)
    @extend_schema(methods=['PUT'], tags=['Orders'], summary="Buyurtma taomlarini to'liq almashtirish",
                   description="Buyurtmadagi barcha taomlarni yangi ro'yxat bilan almashtiradi (edit rejimi uchun). "
                               "Eski taomlar o'chirilib, yangi ro'yxat qo'shiladi va summa qayta hisoblanadi.",
                   request=OrderItemsBulkSerializer)
    @action(detail=True, methods=['post', 'put'], url_path='items')
    def items(self, request, pk=None):
        order = self.get_object()
        self._assert_editable(order, "Yopilgan buyurtma taomlarini o'zgartirib bo'lmaydi")

        if request.method == 'PUT':
            return self._replace_items(order, request)
        return self._add_item(order, request)

    def _add_item(self, order, request):
        serializer = OrderItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        menu_item = MenuItems.objects.get(pk=serializer.validated_data['menu_item_id'])
        quantity = serializer.validated_data['quantity']
        OrderItems.objects.create(
            order=order,
            menu_item=menu_item,
            quantity=quantity,
            price=menu_item.price,
            subtotal=menu_item.price * quantity,
        )
        self._recalculate_total(order)
        # Yangi taom qo'shilganda buyurtma yana "tayyorlanmoqda" bo'ladi
        self._sync_order_status(order)
        return Response(OrderDetailSerializer(order).data)

    def _replace_items(self, order, request):
        serializer = OrderItemsBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        items_data = serializer.validated_data['items']

        with transaction.atomic():
            order.items.all().delete()
            for item_data in items_data:
                menu_item = MenuItems.objects.get(pk=item_data['menu_item_id'])
                quantity = item_data['quantity']
                OrderItems.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=quantity,
                    price=menu_item.price,
                    subtotal=menu_item.price * quantity,
                )
            self._recalculate_total(order)
            self._sync_order_status(order)
        return Response(OrderDetailSerializer(order).data)

    @extend_schema(methods=['PATCH'], tags=['Orders'], summary="Taom miqdorini o'zgartirish",
                   description="Buyurtmadagi bitta taomning miqdorini (quantity) o'zgartiradi va summani qayta hisoblaydi.",
                   request=OrderItemQuantityUpdateSerializer)
    @extend_schema(methods=['DELETE'], tags=['Orders'], summary="Buyurtmadan taom o'chirish",
                   description="Aktiv buyurtmadan taomni o'chiradi va umumiy summani qayta hisoblaydi.")
    @action(detail=True, methods=['patch', 'delete'], url_path=r'items/(?P<item_id>[^/.]+)')
    def item_detail(self, request, pk=None, item_id=None):
        order = self.get_object()
        self._assert_editable(order, "Yopilgan buyurtma taomlarini o'zgartirib bo'lmaydi")

        try:
            item = OrderItems.objects.get(pk=item_id, order=order)
        except OrderItems.DoesNotExist:
            raise NotFound("Buyurtma elementi topilmadi")

        if request.method == 'DELETE':
            item.delete()
            self._recalculate_total(order)
            # Taom o'chgach qolganlari yetkazilgan bo'lsa, buyurtma yetkazildi bo'ladi
            self._sync_order_status(order)
            return Response(OrderDetailSerializer(order).data)

        serializer = OrderItemQuantityUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item.quantity = serializer.validated_data['quantity']
        item.subtotal = item.price * item.quantity
        item.save(update_fields=['quantity', 'subtotal'])
        self._recalculate_total(order)
        return Response(OrderDetailSerializer(order).data)

    @extend_schema(tags=['Orders'], summary="Taom statusini o'zgartirish",
                   description="Buyurtmadagi bitta taomning statusini o'zgartiradi (preparing/delivered/cancelled).",
                   request=OrderItemStatusUpdateSerializer)
    @action(detail=True, methods=['patch'], url_path=r'items/(?P<item_id>[^/.]+)/status')
    def update_item_status(self, request, pk=None, item_id=None):
        order = self.get_object()
        try:
            item = OrderItems.objects.get(pk=item_id, order=order)
        except OrderItems.DoesNotExist:
            raise NotFound("Buyurtma elementi topilmadi")

        serializer = OrderItemStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item.status = serializer.validated_data['status']
        item.save(update_fields=['status'])
        # Hamma taom yetkazilgan bo'lsa buyurtma ham yetkazildi bo'ladi
        self._sync_order_status(order)
        return Response(OrderDetailSerializer(order).data)

    def _recalculate_total(self, order):
        settings = RestaurantSettings.objects.filter(restaurant=order.restaurant).first()
        service_fee_pct = settings.service_fee if settings else 0

        subtotal = sum(item.price * item.quantity for item in order.items.all())
        order.total_amount = subtotal + (subtotal * service_fee_pct / 100)
        order.save(update_fields=['total_amount'])

    def _sync_order_status(self, order):
        """Buyurtma statusini taomlar holatiga qarab avtomatik moslaydi.
        Hamma (bekor qilinmagan) taomlar yetkazilgan bo'lsa -> delivered,
        aks holda -> preparing. Yopilgan/bekor qilingan buyurtma o'zgarmaydi."""
        if order.status in (OrderStatusChoices.CLOSED, OrderStatusChoices.CANCELLED):
            return

        active = [it for it in order.items.all()
                  if it.status != OrderItemStatusChoices.CANCELLED]
        if active and all(it.status == OrderItemStatusChoices.DELIVERED for it in active):
            new_status = OrderStatusChoices.DELIVERED
        else:
            new_status = OrderStatusChoices.PREPARING

        if order.status != new_status:
            order.status = new_status
            order.save(update_fields=['status'])
