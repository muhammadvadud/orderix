from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from order.models import Order, OrderItems
from restaurant.models import Locations

from realtime.broadcast import broadcast_resource_changed


@receiver([post_save, post_delete], sender=Order)
def order_changed(sender, instance, **kwargs):
    broadcast_resource_changed(instance.restaurant_id, 'orders')


@receiver([post_save, post_delete], sender=OrderItems)
def order_item_changed(sender, instance, **kwargs):
    # OrderItems'da restoran order orqali olinadi; order cascade bilan
    # o'chgan bo'lsa Order signali allaqachon xabar bergan, shuning uchun o'tkazib yuboramiz
    try:
        restaurant_id = instance.order.restaurant_id
    except Order.DoesNotExist:
        return
    broadcast_resource_changed(restaurant_id, 'orders')


@receiver([post_save, post_delete], sender=Locations)
def location_changed(sender, instance, **kwargs):
    broadcast_resource_changed(instance.restaurant_id, 'locations')
