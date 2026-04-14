from django.db import models


class Restaurants(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)

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
    restaurant = models.ForeignKey(Restaurants, on_delete=models.CASCADE, related_name='restaurant_settings')
    service_fee = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.restaurant.name

    class Meta:
        db_table = 'restaurant_settings'
        verbose_name = 'Restaurant Settings'
        verbose_name_plural = 'Restaurant Settings'


class Locations(models.Model):
    restaurant = models.ForeignKey(Restaurants, on_delete=models.CASCADE, related_name='locations')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    name = models.CharField(max_length=200)
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

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'menu_items'
        verbose_name = 'Menu Items'
        verbose_name_plural = 'Menu Items'
