from django.urls import path, include
from rest_framework.routers import DefaultRouter

from restaurant.views.restaurant import RestaurantViewSet
from restaurant.views.currency import CurrencyViewSet
from restaurant.views.location import LocationViewSet
from restaurant.views.menu import MenuCategoryViewSet, MenuItemViewSet
from restaurant.views.settings import SettingsView

router = DefaultRouter(trailing_slash=False)
router.register('restaurants', RestaurantViewSet, basename='restaurant')
router.register('currencies', CurrencyViewSet, basename='currency')
router.register('locations', LocationViewSet, basename='location')
router.register('menu/categories', MenuCategoryViewSet, basename='menu-category')
router.register('menu/items', MenuItemViewSet, basename='menu-item')

urlpatterns = [
    path('settings', SettingsView.as_view(), name='settings'),
    path('', include(router.urls)),
]
