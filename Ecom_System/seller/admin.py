from django.contrib import admin
from seller.models import StaffUser, StaffUserProfile, Staff, StaffPrivileges


@admin.register(StaffUser)
class StaffUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'phone', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone')
    readonly_fields = ('created_at',)


@admin.register(StaffUserProfile)
class StaffUserProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'city', 'state', 'pin', 'phone1', 'dob')
    search_fields = ('username__username', 'city', 'aadhaar_number', 'pan_number')


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('staff_id', 'username', 'business_code', 'role', 'phone', 'status', 'created_at')
    list_filter = ('status', 'role', 'business_code')
    search_fields = ('staff_id', 'username__username', 'phone')
    readonly_fields = ('created_at', 'modified_at')


@admin.register(StaffPrivileges)
class StaffPrivilegesAdmin(admin.ModelAdmin):
    list_display = ('staff', 'manage_orders', 'manage_products', 'manage_reports', 'manage_payments')
    list_filter = ('manage_orders', 'manage_products', 'manage_reports', 'manage_payments')
    search_fields = ('staff__staff_id',)
