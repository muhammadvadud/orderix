from django.db import models
from django.contrib.auth.models import AbstractUser
from restaurant.models import Restaurants


class UserRoleChoices(models.TextChoices):
    MANAGER = 'manager', 'Manager'
    WAITER = 'waiter', 'Waiter'
    COOK = 'cook', 'Cook'
    ADMIN = 'admin', 'Admin'


class Account(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True)
    role = models.CharField(
        max_length=10,
        choices=UserRoleChoices,
        default=UserRoleChoices.WAITER
    )
    full_name = models.CharField(max_length=200, blank=True)
    color = models.CharField(max_length=7, default='#2E75B6')
    restaurant = models.ForeignKey(Restaurants, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    tg_id = models.BigIntegerField(unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username

    @property
    def avatar(self):
        source = (self.full_name or self.username or '').strip()
        parts = source.split()
        if not parts:
            return ''
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[1][0]).upper()


class OtpCode(models.Model):
    phone_number = models.CharField(max_length=15, db_index=True)
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.phone_number} - {self.code}'

    class Meta:
        db_table = 'otp_codes'
        verbose_name = 'OTP Code'
        verbose_name_plural = 'OTP Codes'
        ordering = ['-created_at']
