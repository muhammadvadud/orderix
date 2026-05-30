from django.db import migrations


def strip_plus(apps, schema_editor):
    Account = apps.get_model('accounts', 'Account')
    for u in Account.objects.filter(phone_number__startswith='+'):
        u.phone_number = u.phone_number.lstrip('+')
        u.save(update_fields=['phone_number'])


def add_plus(apps, schema_editor):
    Account = apps.get_model('accounts', 'Account')
    for u in Account.objects.exclude(phone_number__startswith='+'):
        u.phone_number = '+' + u.phone_number
        u.save(update_fields=['phone_number'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_otpcode_account_color_account_full_name_and_more'),
    ]

    operations = [
        migrations.RunPython(strip_plus, add_plus),
    ]
