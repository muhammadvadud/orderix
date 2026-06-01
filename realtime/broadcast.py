from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from realtime.consumers import restaurant_group


def broadcast_resource_changed(restaurant_id, resource):
    """Restoran guruhiga resurs o'zgargani haqida xabar yuboradi.
    resource: 'orders' yoki 'locations' — mijoz shu bo'yicha qayta yuklaydi."""
    if restaurant_id is None:
        return
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(
        restaurant_group(restaurant_id),
        {'type': 'resource_changed', 'resource': resource},
    )
