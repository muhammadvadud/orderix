from django.contrib import admin
from .models import Order, OrderItems


class OrderInlines(admin.TabularInline):
    model = OrderItems
    extra = 1


class OrderAdmin(admin.ModelAdmin):
    model = Order
    inlines = [OrderInlines]


admin.site.register(Order, OrderAdmin)
