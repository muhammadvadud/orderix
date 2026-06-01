from channels.generic.websocket import AsyncJsonWebsocketConsumer


def restaurant_group(restaurant_id):
    return f'restaurant_{restaurant_id}'


class RestaurantConsumer(AsyncJsonWebsocketConsumer):
    """Restoran bo'yicha real-time yangilanishlarni yetkazadi.
    Foydalanuvchi o'z restoranining guruhiga qo'shiladi va o'sha guruhga
    yuborilgan 'resource_changed' xabarlarini oladi."""

    async def connect(self):
        user = self.scope.get('user')
        if user is None or not user.is_authenticated:
            await self.close(code=4001)
            return

        restaurant_id = getattr(user, 'restaurant_id', None)
        if restaurant_id is None:
            await self.close(code=4003)
            return

        self.group_name = restaurant_group(restaurant_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        group = getattr(self, 'group_name', None)
        if group:
            await self.channel_layer.group_discard(group, self.channel_name)

    # group_send'dan keladigan {'type': 'resource_changed', ...} xabarini mijozga uzatadi
    async def resource_changed(self, event):
        await self.send_json({
            'event': 'resource_changed',
            'resource': event['resource'],
        })
