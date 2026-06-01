from django.urls import path

from realtime.consumers import RestaurantConsumer

websocket_urlpatterns = [
    path('ws/realtime/', RestaurantConsumer.as_asgi()),
]
