from django.contrib import admin
from .models import Account


class UserRole(admin.ModelAdmin):
    list_display = ('username', 'phone_number', 'role')


admin.site.register(Account, UserRole)