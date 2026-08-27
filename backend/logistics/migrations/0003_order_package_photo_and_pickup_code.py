import secrets
from django.db import migrations, models
import logistics.models


def populate_pickup_codes(apps, schema_editor):
    Order = apps.get_model('logistics', 'Order')
    used = set(Order.objects.exclude(pickup_code__isnull=True).values_list('pickup_code', flat=True))
    for order in Order.objects.filter(pickup_code__isnull=True).iterator():
        while True:
            code = f'{secrets.randbelow(1_000_000):06d}'
            if code not in used:
                used.add(code)
                order.pickup_code = code
                order.save(update_fields=['pickup_code'])
                break


class Migration(migrations.Migration):
    dependencies = [('logistics', '0002_pricingconfiguration_order_price_per_kg_and_more')]

    operations = [
        migrations.AddField(
            model_name='order',
            name='package_photo',
            field=models.ImageField(blank=True, null=True, upload_to='orders/packages/'),
        ),
        migrations.AddField(
            model_name='order',
            name='pickup_code',
            field=models.CharField(editable=False, max_length=6, null=True),
        ),
        migrations.RunPython(populate_pickup_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='order',
            name='pickup_code',
            field=models.CharField(default=logistics.models.generate_pickup_code, editable=False, max_length=6, unique=True),
        ),
    ]
