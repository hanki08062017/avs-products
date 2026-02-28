# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0007_order_address_fields'),
        ('users', '0002_savedaddress_savedpaymentmethod'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='bill_name',
            field=models.CharField(max_length=255, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='bill_phone',
            field=models.CharField(max_length=20, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='ship_name',
            field=models.CharField(max_length=255, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='ship_phone',
            field=models.CharField(max_length=20, default=''),
            preserve_default=False,
        ),
    ]
