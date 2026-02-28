from django.contrib import admin
from .models import BusinessDetail, StaffUser, StaffUserProfile, GSTDetail, Staff, ProductCategory, Product, Order, Payment, UnitOfMeasurement, Wallet, ProductImage

admin.site.register(BusinessDetail)
admin.site.register(GSTDetail)
admin.site.register(Staff)
admin.site.register(ProductCategory)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(Order)
admin.site.register(Payment)
admin.site.register(UnitOfMeasurement)
admin.site.register(Wallet)
admin.site.register(StaffUser)
admin.site.register(StaffUserProfile)
