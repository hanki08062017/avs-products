from django.contrib import admin
from management.models import (
    BusinessDetail, GSTDetail, ProductCategory, Product, ProductImage,
    Order, Payment, UnitOfMeasurement, Wallet, WalletTransaction,
    Refund, DeliverySettings, DeliveryZone, ManagementUser, WalletAPIConfig
)

admin.site.site_header = "AVS Management Dashboard"
admin.site.site_title = "AVS Admin"
admin.site.index_title = "Welcome to AVS Admin Panel"


@admin.register(BusinessDetail)
class BusinessDetailAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'code', 'business_type', 'mode', 'city', 'state', 'status')
    list_filter = ('business_type', 'mode', 'status')
    search_fields = ('business_name', 'code', 'city', 'state')


@admin.register(GSTDetail)
class GSTDetailAdmin(admin.ModelAdmin):
    list_display = ('gst_number', 'pan', 'business_code', 'reg_date', 'valid_till', 'city', 'status')
    list_filter = ('status',)
    search_fields = ('gst_number', 'pan', 'business_code__code')


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('category', 'sub_category', 'hsn', 'sgst', 'cgst')
    search_fields = ('category', 'sub_category', 'hsn')


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    readonly_fields = ('image',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_name', 'product_category', 'mrp', 'selling_price', 'stock', 'status', 'business_code')
    list_filter = ('status', 'business_code', 'product_category')
    search_fields = ('id', 'product_name', 'manufacturer', 'source')
    inlines = [ProductImageInline]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_primary', 'created_at')
    list_filter = ('is_primary',)
    search_fields = ('product__product_name',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'customer_name', 'customer_phone', 'total_amount', 'order_status', 'payment_method', 'payment_status', 'placed_at')
    list_filter = ('order_status', 'payment_method', 'payment_status', 'placed_type', 'order_type')
    search_fields = ('order_id', 'customer_name', 'customer_email', 'customer_phone', 'invoice_no')
    readonly_fields = ('placed_at', 'created_at', 'modified_at')
    date_hierarchy = 'placed_at'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'reference_order', 'amount', 'payment_mode', 'transaction_type', 'status', 'created_at')
    list_filter = ('status', 'payment_mode', 'transaction_type')
    search_fields = ('transaction_id', 'reference_order__order_id', 'avs_wallet_id')
    readonly_fields = ('created_at', 'modified_at')


@admin.register(UnitOfMeasurement)
class UnitOfMeasurementAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'created_by', 'created_at')
    search_fields = ('name', 'abbreviation')


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('wallet_id', 'customer_name', 'customer_id', 'customer_mobile', 'wallet_type', 'created_at')
    list_filter = ('wallet_type',)
    search_fields = ('wallet_id', 'customer_name', 'customer_id', 'customer_mobile')


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'avs_customer_name', 'avs_customer_id', 'transaction_type', 'amount', 'transaction_date')
    list_filter = ('transaction_type',)
    search_fields = ('transaction_id', 'avs_customer_name', 'avs_customer_id')
    date_hierarchy = 'transaction_date'


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('id', 'reference_order', 'amount', 'payment_mode', 'refund_status', 'created_at')
    list_filter = ('refund_status', 'payment_mode')
    search_fields = ('reference_order__order_id', 'created_by')
    readonly_fields = ('created_at', 'modified_at')


@admin.register(DeliverySettings)
class DeliverySettingsAdmin(admin.ModelAdmin):
    list_display = ('business_code', 'store_city', 'store_pin', 'delivery_free', 'ship_free', 'max_distance_km')


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ('zone_name', 'business_code', 'pincode_to', 'distance_range_km', 'base_charge', 'status')
    list_filter = ('status', 'business_code')
    search_fields = ('zone_name', 'pincode_to')


@admin.register(ManagementUser)
class ManagementUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'phone', 'role', 'status', 'last_login')
    list_filter = ('role', 'status')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    readonly_fields = ('last_login',)


@admin.register(WalletAPIConfig)
class WalletAPIConfigAdmin(admin.ModelAdmin):
    list_display = ('config_name', 'source_name', 'status', 'created_by', 'created_at')
    list_filter = ('status',)
    search_fields = ('config_name', 'source_name')
    readonly_fields = ('created_at', 'modified_at')
