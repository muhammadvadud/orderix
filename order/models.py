from django.db import models
from restaurant.models import Restaurants, Locations
from django.contrib.auth import get_user_model


class Order(models.Model):
    waiter = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='orders')
    restaurant = models.ForeignKey(Restaurants, on_delete=models.CASCADE, related_name='orders')
    location = models.ForeignKey(Locations, on_delete=models.CASCADE, related_name='orders')
    status = models.BooleanField(default=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    created = models.DateTimeField(auto_now_add=True)
    closed = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.pk)


class OrderItems(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    restaurant = models.ForeignKey(Restaurants, on_delete=models.CASCADE, related_name='items')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return str(self.pk)

    class Meta:
        db_table = 'order_items'
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
