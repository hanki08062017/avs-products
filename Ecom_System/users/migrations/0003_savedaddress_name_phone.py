# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_savedaddress_savedpaymentmethod'),
    ]

    operations = [
        migrations.AddField(
            model_name='savedaddress',
            name='name',
            field=models.CharField(max_length=255, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='savedaddress',
            name='phone',
            field=models.CharField(max_length=20, default=''),
            preserve_default=False,
        ),
    ]
