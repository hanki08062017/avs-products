from django.contrib import admin
from .models import  Customer, CustomerProfile, SavedAddress, SavedPaymentMethod

admin.site.register(Customer)
admin.site.register(CustomerProfile)
admin.site.register(SavedAddress)
admin.site.register(SavedPaymentMethod)