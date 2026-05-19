from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0002_order_status_orderitems_menu_item'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='order',
            options={'verbose_name': 'Order', 'verbose_name_plural': 'Orders'},
        ),
        migrations.AlterField(
            model_name='order',
            name='total_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
    ]
