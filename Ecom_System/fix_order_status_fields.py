"""
Script to fix existing orders' placed_by and confirmed_by fields
Run this once to update all existing orders in the database
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Ecom_System.settings')
django.setup()

from business.models import Order

# Fix all orders
orders = Order.objects.all()
updated_count = 0

for order in orders:
    updated = False
    
    # Fix placed_by if it's empty
    if not order.placed_by:
        order.placed_by = order.customer_name
        updated = True
    
    # Fix confirmed_by for orders with successful payment
    if order.order_status == 'Confirmed' and order.payment_status == 'Successful':
        if not order.confirmed_by or order.confirmed_by == order.customer_name:
            order.confirmed_by = 'System'
            updated = True
    
    if updated:
        # Save without triggering the save method logic
        Order.objects.filter(pk=order.pk).update(
            placed_by=order.placed_by,
            confirmed_by=order.confirmed_by if order.order_status == 'Confirmed' else order.confirmed_by
        )
        updated_count += 1
        print(f"Updated order {order.order_id}")

print(f"\nTotal orders updated: {updated_count}")
