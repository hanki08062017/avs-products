"""
Script to check and fix specific order ORD20260308175131336227
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Ecom_System.settings')
django.setup()

from business.models import Order

# Check the specific order
order_id = 'ORD20260308175131336227'
try:
    order = Order.objects.get(pk=order_id)
    print(f"Order ID: {order.order_id}")
    print(f"Customer Name: {order.customer_name}")
    print(f"Order Status: {order.order_status}")
    print(f"Payment Status: {order.payment_status}")
    print(f"Placed By: {order.placed_by}")
    print(f"Confirmed By: {order.confirmed_by}")
    print(f"Confirmed At: {order.confirmed_at}")
    
    # Fix if needed
    if order.order_status == 'Confirmed' and order.payment_status == 'Successful':
        if order.confirmed_by != 'System':
            print(f"\nFixing confirmed_by from '{order.confirmed_by}' to 'System'")
            Order.objects.filter(pk=order_id).update(confirmed_by='System')
            print("Updated successfully!")
        else:
            print("\nOrder is already correct!")
    
except Order.DoesNotExist:
    print(f"Order {order_id} not found")
