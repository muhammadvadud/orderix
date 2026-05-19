import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0001_initial'),
        ('restaurant', '0002_restaurant_deleted_at_menuitem_deleted_at'),
    ]

    operations = [
        # 1. Order.status: BooleanField -> CharField
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('open', 'Open'),
                    ('in_progress', 'In Progress'),
                    ('closed', 'Closed'),
                    ('cancelled', 'Cancelled'),
                ],
                default='open',
                max_length=20,
            ),
        ),
        # 2. Order meta
        migrations.AlterModelTable(
            name='order',
            table='orders',
        ),
        # 3. Add menu_item nullable first (existing rows)
        migrations.AddField(
            model_name='orderitems',
            name='menu_item',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='order_items',
                to='restaurant.menuitems',
            ),
        ),
        # 4. Remove old restaurant FK from OrderItems
        migrations.RemoveField(
            model_name='orderitems',
            name='restaurant',
        ),
        # 5. Make menu_item non-nullable
        migrations.AlterField(
            model_name='orderitems',
            name='menu_item',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='order_items',
                to='restaurant.menuitems',
            ),
        ),
    ]
