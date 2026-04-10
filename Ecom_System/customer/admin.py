from django.contrib import admin
from customer.models import Customer, CustomerProfile, SavedAddress, SavedPaymentMethod


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'phone', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone')
    readonly_fields = ('created_at',)


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'city', 'state', 'pin', 'phone1')
    search_fields = ('username__username', 'city', 'state', 'pin')


@admin.register(SavedAddress)
class SavedAddressAdmin(admin.ModelAdmin):
    list_display = ('customer', 'name', 'address_type', 'city', 'state', 'pin', 'is_default')
    list_filter = ('address_type', 'is_default')
    search_fields = ('customer__username', 'name', 'city', 'pin')


@admin.register(SavedPaymentMethod)
class SavedPaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('customer', 'payment_type', 'card_last4', 'upi_id', 'is_default')
    list_filter = ('payment_type', 'is_default')
    search_fields = ('customer__username', 'upi_id')
