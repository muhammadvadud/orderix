from django.db import models


class Restaurants(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'restaurants'
        verbose_name = 'Restaurants'
        verbose_name_plural = 'Restaurants'


class Currency(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'currency'
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'


class RestaurantSettings(models.Model):
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='currency')
    restaurant = models.ForeignKey(Restaurants, on_delete=models.CASCADE, related_name='restaurant_settings', unique=True)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2)
    notify_orders = models.BooleanField(default=True)
    notify_staff = models.BooleanField(default=False)
    notify_daily = models.BooleanField(default=True)

    def __str__(self):
        return self.restaurant.name

    class Meta:
        db_table = 'restaurant_settings'
        verbose_name = 'Restaurant Settings'
        verbose_name_plural = 'Restaurant Settings'


class LocationTypeChoices(models.TextChoices):
    ZONE = 'zone', 'Zone'
    TABLE = 'table', 'Table'


class TableStatusChoices(models.TextChoices):
    FREE = 'free', 'Free'
    OCCUPIED = 'occupied', 'Occupied'
    RESERVED = 'reserved', 'Reserved'
    DIRTY = 'dirty', 'Dirty'


class Locations(models.Model):
    restaurant = models.ForeignKey(Restaurants, on_delete=models.CASCADE, related_name='locations')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    type = models.CharField(
        max_length=10,
        choices=LocationTypeChoices.choices,
        default=LocationTypeChoices.ZONE
    )
    name = models.CharField(max_length=200)
    short = models.CharField(max_length=8, blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, blank=True)
    number = models.PositiveIntegerField(null=True, blank=True)
    seats = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=TableStatusChoices,
        default=TableStatusChoices.FREE
    )
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'locations'
        verbose_name = 'Locations'
        verbose_name_plural = 'Locations'


class MenuCategory(models.Model):
    restaurant = models.ForeignKey(Restaurants, on_delete=models.CASCADE, related_name='menu_category')
    name = models.CharField(max_length=200)
    icon = models.CharField(max_length=50, default='Utensils')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'menu_category'
        verbose_name = 'Menu Category'
        verbose_name_plural = 'Menu Categories'


class MenuItems(models.Model):
    restaurant = models.ForeignKey(Restaurants, on_delete=models.CASCADE, related_name='menu_items')
    category = models.ForeignKey(MenuCategory, on_delete=models.CASCADE, related_name='menu_items')
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'menu_items'
        verbose_name = 'Menu Items'
        verbose_name_plural = 'Menu Items'
