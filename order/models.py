from django.db import models
from restaurant.models import Restaurants, Locations, MenuItems
from django.contrib.auth import get_user_model


class OrderStatusChoices(models.TextChoices):
    PREPARING = 'preparing', 'Preparing'
    DELIVERED = 'delivered', 'Delivered'
    CLOSED = 'closed', 'Closed'
    CANCELLED = 'cancelled', 'Cancelled'


class OrderItemStatusChoices(models.TextChoices):
    PREPARING = 'preparing', 'Preparing'
    DELIVERED = 'delivered', 'Delivered'
    CANCELLED = 'cancelled', 'Cancelled'


class Order(models.Model):
    waiter = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='orders')
    restaurant = models.ForeignKey(Restaurants, on_delete=models.CASCADE, related_name='orders')
    location = models.ForeignKey(Locations, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(
        max_length=20,
        choices=OrderStatusChoices.choices,
        default=OrderStatusChoices.PREPARING
    )
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    # Buyurtma yaratilgan paytdagi restoran xizmat haqi (%) — keyin sozlama o'zgarsa ham shu saqlanadi
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created = models.DateTimeField(auto_now_add=True)
    closed = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.pk)

    class Meta:
        db_table = 'orders'
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'


class OrderItems(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItems, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=OrderItemStatusChoices.choices,
        default=OrderItemStatusChoices.PREPARING
    )

    def __str__(self):
        return str(self.pk)

    class Meta:
        db_table = 'order_items'
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
