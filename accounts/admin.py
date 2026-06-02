from django.contrib import admin
from .models import Account, OtpCode


class UserRole(admin.ModelAdmin):
    list_display = ('id', 'username', 'phone_number', 'role')


admin.site.register(Account, UserRole)
admin.site.register(OtpCode)
