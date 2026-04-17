from django.contrib import admin
from .models import Restaurants, RestaurantSettings, Locations

admin.site.register(Restaurants)
admin.site.register(RestaurantSettings)
admin.site.register(Locations)
