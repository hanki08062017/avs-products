# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0006_product_business_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='bill_address',
        ),
        migrations.RemoveField(
            model_name='order',
            name='ship_address',
        ),
        migrations.AddField(
            model_name='order',
            name='bill_address1',
            field=models.CharField(max_length=255, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='bill_address2',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='bill_city',
            field=models.CharField(max_length=100, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='bill_state',
            field=models.CharField(max_length=100, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='bill_pin',
            field=models.CharField(max_length=10, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='bill_country',
            field=models.CharField(default='India', max_length=100),
        ),
        migrations.AddField(
            model_name='order',
            name='ship_address1',
            field=models.CharField(max_length=255, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='ship_address2',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='ship_city',
            field=models.CharField(max_length=100, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='ship_state',
            field=models.CharField(max_length=100, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='ship_pin',
            field=models.CharField(max_length=10, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='ship_country',
            field=models.CharField(default='India', max_length=100),
        ),
    ]
