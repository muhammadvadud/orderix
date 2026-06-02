from django.contrib import admin
from .models import Restaurants, RestaurantSettings, Locations, MenuItems, MenuCategory

admin.site.register(Restaurants)
admin.site.register(RestaurantSettings)
admin.site.register(Locations)
admin.site.register(MenuItems)
admin.site.register(MenuCategory)
