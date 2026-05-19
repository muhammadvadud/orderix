from django.urls import path, include
from rest_framework.routers import DefaultRouter

from order.views.order import OrderViewSet

router = DefaultRouter(trailing_slash=False)
router.register('orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
]
