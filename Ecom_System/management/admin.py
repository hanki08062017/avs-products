from django.contrib import admin
from management.models import BusinessDetail, GSTDetail, ProductCategory, Product, Order, Payment, UnitOfMeasurement, Wallet, ProductImage, Refund, DeliverySettings

admin.site.register(BusinessDetail)
admin.site.register(GSTDetail)
admin.site.register(ProductCategory)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(Order)
admin.site.register(Payment)
admin.site.register(UnitOfMeasurement)
admin.site.register(Wallet)
admin.site.register(Refund)
admin.site.register(DeliverySettings)
