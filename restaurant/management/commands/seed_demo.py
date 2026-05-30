from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Account, UserRoleChoices
from restaurant.models import (
    Restaurants, Currency, RestaurantSettings,
    Locations, LocationTypeChoices, TableStatusChoices,
    MenuCategory, MenuItems,
)
from order.models import Order, OrderItems, OrderStatusChoices

DEMO_RESTAURANT = 'OrderiX Demo'


class Command(BaseCommand):
    help = "Frontend mock'iga mos demo ma'lumotlarni yaratadi (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        restaurant, _ = Restaurants.objects.get_or_create(
            name=DEMO_RESTAURANT, defaults={'phone': '+998901112233'})

        currency, _ = Currency.objects.get_or_create(name="So'm", defaults={'code': 'UZS'})
        RestaurantSettings.objects.get_or_create(
            restaurant=restaurant,
            defaults={'currency': currency, 'service_fee': Decimal('10.00')},
        )

        self._seed_staff(restaurant)
        zones = self._seed_locations(restaurant)
        categories = self._seed_menu(restaurant)
        self._seed_orders(restaurant, zones, categories)

        self.stdout.write(self.style.SUCCESS(f"Demo ma'lumotlar tayyor: {DEMO_RESTAURANT}"))

    def _seed_staff(self, restaurant):
        staff = [
            ('+998931000001', 'manager_demo', 'Aziza Karimova', UserRoleChoices.MANAGER, '#2E75B6'),
            ('+998931000002', 'waiter_demo1', 'Bekzod Aliyev', UserRoleChoices.WAITER, '#27AE60'),
            ('+998931000003', 'waiter_demo2', 'Dilnoza Yusupova', UserRoleChoices.WAITER, '#E67E22'),
            ('+998931000004', 'cook_demo', 'Sardor Tursunov', UserRoleChoices.COOK, '#8E44AD'),
        ]
        for phone, username, full_name, role, color in staff:
            user, created = Account.objects.get_or_create(
                phone_number=phone,
                defaults={'username': username, 'full_name': full_name, 'role': role,
                          'color': color, 'restaurant': restaurant},
            )
            if created:
                user.set_password('demo12345')
                user.save()

    def _seed_locations(self, restaurant):
        zones_data = [
            ('Asosiy zal', 'AZ', 'Utensils', '#2E75B6', [(1, 4), (2, 2), (3, 6)]),
            ('Terassa', 'TR', 'Trees', '#27AE60', [(4, 4), (5, 4)]),
            ('VIP', 'VIP', 'Crown', '#8E44AD', [(6, 8)]),
        ]
        zones = {}
        for name, short, icon, color, tables in zones_data:
            zone, _ = Locations.objects.get_or_create(
                restaurant=restaurant, type=LocationTypeChoices.ZONE, name=name,
                defaults={'short': short, 'icon': icon, 'color': color},
            )
            zones[name] = zone
            for number, seats in tables:
                Locations.objects.get_or_create(
                    restaurant=restaurant, type=LocationTypeChoices.TABLE,
                    parent=zone, number=number,
                    defaults={'name': f'{number}-stol', 'seats': seats,
                              'status': TableStatusChoices.FREE},
                )
        return zones

    def _seed_menu(self, restaurant):
        menu = {
            ('Taomlar', 'UtensilsCrossed'): [('Osh', 35000), ('Lag\'mon', 30000), ('Manti', 28000)],
            ('Ichimliklar', 'CupSoda'): [('Choy', 5000), ('Coca-Cola', 12000)],
            ('Salatlar', 'Salad'): [('Achichuk', 15000), ('Sezar', 32000)],
        }
        categories = {}
        for (cat_name, icon), items in menu.items():
            category, _ = MenuCategory.objects.get_or_create(
                restaurant=restaurant, name=cat_name, defaults={'icon': icon})
            categories[cat_name] = category
            for item_name, price in items:
                MenuItems.objects.get_or_create(
                    restaurant=restaurant, category=category, name=item_name,
                    defaults={'price': Decimal(price)},
                )
        return categories

    def _seed_orders(self, restaurant, zones, categories):
        if Order.objects.filter(restaurant=restaurant).exists():
            return
        waiter = Account.objects.filter(restaurant=restaurant, role=UserRoleChoices.WAITER).first()
        table = Locations.objects.filter(
            restaurant=restaurant, type=LocationTypeChoices.TABLE).first()
        osh = MenuItems.objects.filter(restaurant=restaurant, name='Osh').first()
        if not (waiter and table and osh):
            return

        order = Order.objects.create(
            waiter=waiter, restaurant=restaurant, location=table,
            status=OrderStatusChoices.PREPARING,
        )
        OrderItems.objects.create(
            order=order, menu_item=osh, quantity=2,
            price=osh.price, subtotal=osh.price * 2,
        )
        settings = RestaurantSettings.objects.filter(restaurant=restaurant).first()
        fee = settings.service_fee if settings else 0
        subtotal = osh.price * 2
        order.total_amount = subtotal + (subtotal * fee / 100)
        order.save(update_fields=['total_amount'])
