from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0006_alter_businessdetail_business_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeliveryZone',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('zone_name', models.CharField(max_length=100)),
                ('pincode_from', models.CharField(max_length=10)),
                ('pincode_to', models.CharField(max_length=10)),
                ('distance_range_km', models.CharField(max_length=50)),
                ('base_charge', models.DecimalField(decimal_places=2, max_digits=10)),
                ('estimated_days_min', models.IntegerField(default=1)),
                ('estimated_days_max', models.IntegerField(default=3)),
                ('status', models.CharField(choices=[('Active', 'Active'), ('Inactive', 'Inactive')], default='Active', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(max_length=100)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('modified_by', models.CharField(blank=True, max_length=100, null=True)),
                ('business_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='management.businessdetail', to_field='code')),
            ],
            options={'db_table': 'business_deliveryzone'},
        ),
        migrations.CreateModel(
            name='DeliveryWeightSlab',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('slab_name', models.CharField(max_length=100)),
                ('weight_from_kg', models.DecimalField(decimal_places=2, max_digits=8)),
                ('weight_to_kg', models.DecimalField(decimal_places=2, max_digits=8)),
                ('extra_charge', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('Active', 'Active'), ('Inactive', 'Inactive')], default='Active', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(max_length=100)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('modified_by', models.CharField(blank=True, max_length=100, null=True)),
                ('business_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='management.businessdetail', to_field='code')),
            ],
            options={'db_table': 'business_deliveryweightslab'},
        ),
    ]
