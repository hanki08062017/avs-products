"""
Script to fix ALL orders with missing placed_by field
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Ecom_System.settings')
django.setup()

from business.models import Order

# Find all orders with empty placed_by
orders_to_fix = Order.objects.filter(placed_by__isnull=True) | Order.objects.filter(placed_by='')
print(f"Found {orders_to_fix.count()} orders with empty placed_by")

for order in orders_to_fix:
    print(f"Fixing order {order.order_id}: placed_by = '{order.customer_name}'")
    Order.objects.filter(pk=order.pk).update(placed_by=order.customer_name)

print("\nNow checking all Placed orders:")
placed_orders = Order.objects.filter(order_status='Placed')
for order in placed_orders:
    print(f"Order {order.order_id}: Status={order.order_status}, Placed By={order.placed_by}")
    if not order.placed_by:
        print(f"  -> Fixing: Setting placed_by to '{order.customer_name}'")
        Order.objects.filter(pk=order.pk).update(placed_by=order.customer_name)

print("\nDone!")
