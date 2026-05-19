from django.db import models
from django.contrib.auth.models import AbstractUser
from restaurant.models import Restaurants


class UserRoleChoices(models.TextChoices):
    MANAGER = 'manager', 'Manager'
    WAITER = 'waiter', 'Waiter'
    ADMIN = 'admin', 'Admin'


class Account(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True)
    role = models.CharField(
        max_length=10,
        choices=UserRoleChoices,
        default=UserRoleChoices.WAITER
    )
    restaurant = models.ForeignKey(Restaurants, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    tg_id = models.IntegerField(unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username
