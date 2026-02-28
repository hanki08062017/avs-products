# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SavedAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address_type', models.CharField(choices=[('Billing', 'Billing'), ('Shipping', 'Shipping'), ('Both', 'Both')], max_length=20)),
                ('address1', models.CharField(max_length=255)),
                ('address2', models.CharField(blank=True, max_length=255, null=True)),
                ('city', models.CharField(max_length=100)),
                ('state', models.CharField(max_length=100)),
                ('pin', models.CharField(max_length=10)),
                ('country', models.CharField(default='India', max_length=100)),
                ('is_default', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_addresses', to='users.customer', to_field='username')),
            ],
            options={
                'db_table': 'saved_address',
            },
        ),
        migrations.CreateModel(
            name='SavedPaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_type', models.CharField(choices=[('Card', 'Card'), ('UPI', 'UPI')], max_length=20)),
                ('card_last4', models.CharField(blank=True, max_length=4, null=True)),
                ('card_name', models.CharField(blank=True, max_length=255, null=True)),
                ('upi_id', models.CharField(blank=True, max_length=255, null=True)),
                ('is_default', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_payments', to='users.customer', to_field='username')),
            ],
            options={
                'db_table': 'saved_payment_method',
            },
        ),
    ]
