import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Ecom_System.settings')
django.setup()

from business.models import BusinessDetail, ProductCategory, Product, Staff, StaffUser

# Create Business
business, _ = BusinessDetail.objects.get_or_create(
    code='B001',
    defaults={
        'business_name': 'Harendra Electronics',
        'business_type': 'Shop',
        'symbol': 'HE',
        'mode': 'Online',
        'address': '123 Main Street',
        'city': 'Mumbai',
        'state': 'Maharashtra',
        'pin': '400001',
        'country': 'India',
        'status': 'Active'
    }
)

# Create Staff User
staff_user, created = StaffUser.objects.get_or_create(
    username='harendra',
    defaults={
        'first_name': 'Harendra',
        'last_name': 'Sharma',
        'email': 'harendra@example.com',
        'phone': '9876543210',
        'password': 'password123',
        'status': True
    }
)

# Create Staff
staff, _ = Staff.objects.get_or_create(
    staff_id='S001',
    defaults={
        'username': staff_user,
        'business_code': business,
        'staff_role': 'Seller-Admin',
        'phone': '9876543210',
        'created_by': 'admin',
        'status': 'Active'
    }
)

# Create Product Categories
categories_data = [
    {'category': 'Electronics', 'sub_category': 'Mobile Phones', 'hsn': '8517', 'sgst': 9, 'cgst': 9},
    {'category': 'Electronics', 'sub_category': 'Laptops', 'hsn': '8471', 'sgst': 9, 'cgst': 9},
    {'category': 'Home Appliances', 'sub_category': 'Refrigerators', 'hsn': '8418', 'sgst': 14, 'cgst': 14},
    {'category': 'Home Appliances', 'sub_category': 'Washing Machines', 'hsn': '8450', 'sgst': 14, 'cgst': 14},
]

categories = []
for cat_data in categories_data:
    cat, _ = ProductCategory.objects.get_or_create(
        category=cat_data['category'],
        sub_category=cat_data['sub_category'],
        defaults={
            'hsn': cat_data['hsn'],
            'sgst': cat_data['sgst'],
            'cgst': cat_data['cgst'],
            'created_by': 'harendra'
        }
    )
    categories.append(cat)

# Create Products
products_data = [
    {'name': 'Samsung Galaxy S23', 'category': 0, 'qty': 1, 'unit': 'pcs', 'mrp': 79999, 'cost': 70000, 'selling': 74999, 'stock': 15, 'source': 'Samsung India', 'manufacturer': 'Samsung'},
    {'name': 'iPhone 14', 'category': 0, 'qty': 1, 'unit': 'pcs', 'mrp': 89999, 'cost': 80000, 'selling': 84999, 'stock': 10, 'source': 'Apple India', 'manufacturer': 'Apple'},
    {'name': 'OnePlus 11', 'category': 0, 'qty': 1, 'unit': 'pcs', 'mrp': 56999, 'cost': 50000, 'selling': 54999, 'stock': 20, 'source': 'OnePlus', 'manufacturer': 'OnePlus'},
    {'name': 'Dell Inspiron 15', 'category': 1, 'qty': 1, 'unit': 'pcs', 'mrp': 65999, 'cost': 58000, 'selling': 62999, 'stock': 8, 'source': 'Dell India', 'manufacturer': 'Dell'},
    {'name': 'HP Pavilion', 'category': 1, 'qty': 1, 'unit': 'pcs', 'mrp': 55999, 'cost': 49000, 'selling': 52999, 'stock': 12, 'source': 'HP India', 'manufacturer': 'HP'},
    {'name': 'Lenovo ThinkPad', 'category': 1, 'qty': 1, 'unit': 'pcs', 'mrp': 75999, 'cost': 68000, 'selling': 72999, 'stock': 6, 'source': 'Lenovo', 'manufacturer': 'Lenovo'},
    {'name': 'LG 260L Refrigerator', 'category': 2, 'qty': 1, 'unit': 'pcs', 'mrp': 28999, 'cost': 24000, 'selling': 26999, 'stock': 5, 'source': 'LG India', 'manufacturer': 'LG'},
    {'name': 'Samsung 7kg Washing Machine', 'category': 3, 'qty': 1, 'unit': 'pcs', 'mrp': 22999, 'cost': 19000, 'selling': 20999, 'stock': 7, 'source': 'Samsung India', 'manufacturer': 'Samsung'},
    {'name': 'Whirlpool 6.5kg Washing Machine', 'category': 3, 'qty': 1, 'unit': 'pcs', 'mrp': 18999, 'cost': 16000, 'selling': 17499, 'stock': 10, 'source': 'Whirlpool', 'manufacturer': 'Whirlpool'},
    {'name': 'Haier 190L Refrigerator', 'category': 2, 'qty': 1, 'unit': 'pcs', 'mrp': 18999, 'cost': 15500, 'selling': 17499, 'stock': 8, 'source': 'Haier India', 'manufacturer': 'Haier'},
]

for prod_data in products_data:
    Product.objects.get_or_create(
        product_name=prod_data['name'],
        defaults={
            'description': f'{prod_data["name"]} - High quality product',
            'product_category': categories[prod_data['category']],
            'quantity': prod_data['qty'],
            'unit': prod_data['unit'],
            'mrp': prod_data['mrp'],
            'cost_price': prod_data['cost'],
            'selling_price': prod_data['selling'],
            'stock': prod_data['stock'],
            'source': prod_data['source'],
            'manufacturer': prod_data['manufacturer'],
            'status': 'Active',
            'created_by': 'harendra'
        }
    )

print("Successfully created:")
print(f"   - Business: {business.business_name} ({business.code})")
print(f"   - Staff User: {staff_user.first_name} {staff_user.last_name} (username: {staff_user.username})")
print(f"   - Staff: {staff.staff_id} - {staff.staff_role}")
print(f"   - Categories: {len(categories)}")
print(f"   - Products: {Product.objects.count()}")
print(f"\nLogin credentials:")
print(f"   Username: harendra")
print(f"   Password: password123")
print(f"   Business Code: B001")
