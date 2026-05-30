from django.db import migrations


def remap_status_forward(apps, schema_editor):
    Order = apps.get_model('order', 'Order')
    Order.objects.filter(status='open').update(status='preparing')
    Order.objects.filter(status='in_progress').update(status='delivered')


def remap_status_backward(apps, schema_editor):
    Order = apps.get_model('order', 'Order')
    Order.objects.filter(status='preparing').update(status='open')
    Order.objects.filter(status='delivered').update(status='in_progress')


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0004_orderitems_status_alter_order_status'),
    ]

    operations = [
        migrations.RunPython(remap_status_forward, remap_status_backward),
    ]
