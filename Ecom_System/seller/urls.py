from django.urls import path
from . import views
from .config_views import config_view, add_category, edit_category, add_unit, edit_unit, add_gst, edit_gst, add_delivery_zone, edit_delivery_zone, add_weight_slab, edit_weight_slab, check_delivery_charge, save_delivery_settings


urlpatterns = [
    path('staff-login/', views.staff_login, name='staff_login'),
    path('staff-logout/', views.staff_logout, name='staff_logout'),
    path('<str:username>/staff_profile/', views.seller_profile_view, name='seller_profile'),
    
    
    
    
    
    
    path('seller/', views.seller_dashboard, name='seller_dashboard'),
 
    path('seller/config/', config_view, name='config'),
    path('seller/config/add-category/', add_category, name='add_category'),
    path('seller/config/edit-category/<int:id>/', edit_category, name='edit_category'),
    path('seller/config/add-unit/', add_unit, name='add_unit'),
    path('seller/config/edit-unit/<int:id>/', edit_unit, name='edit_unit'),
    path('seller/config/add-gst/', add_gst, name='add_gst'),
    path('seller/config/edit-gst/<int:id>/', edit_gst, name='edit_gst'),
    path('seller/config/save-delivery-settings/', save_delivery_settings, name='save_delivery_settings'),
    path('seller/config/add-delivery-zone/', add_delivery_zone, name='add_delivery_zone'),
    path('seller/config/edit-delivery-zone/<int:id>/', edit_delivery_zone, name='edit_delivery_zone'),
    path('seller/config/add-weight-slab/', add_weight_slab, name='add_weight_slab'),
    path('seller/config/edit-weight-slab/<int:id>/', edit_weight_slab, name='edit_weight_slab'),
    path('seller/config/check-delivery-charge/', check_delivery_charge, name='check_delivery_charge'),
    path('seller/add-stock/', views.add_stock, name='add_stock'),
    path('seller/add-product/', views.add_product, name='add_product'),
    path('seller/view-product/<str:product_id>/', views.view_product, name='view_product'),
    path('seller/edit-product/<str:product_id>/', views.edit_product, name='edit_product'),
    path('remove-product-image/<int:image_id>/', views.remove_product_image, name='remove_product_image'),
    path('set-primary-image/<int:image_id>/', views.set_primary_image, name='set_primary_image'),
    path('seller/orders/', views.manage_orders, name='manage_orders'),
    path('seller/update-order-status/<str:order_id>/', views.update_order_status, name='update_order_status'),
    path('seller/update-seller-payment-status/', views.update_seller_payment_status, name='update_seller_payment_status'),
    path('seller/update-refund-status/', views.update_refund_status, name='update_refund_status'),
    path('seller/order-details/<str:order_id>/', views.order_details, name='order_details'),
    path('seller/add-staff/', views.add_staff, name='add_staff'),
    path('seller/view-staff/<str:staff_id>/', views.view_staff, name='view_staff'),
    path('seller/edit-staff/<str:staff_id>/', views.edit_staff, name='edit_staff'),
    path('management/', views.management_dashboard, name='management_dashboard'),
    
    path('delete-address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('edit-address/<int:address_id>/', views.edit_address, name='edit_address'),
    
    path('seller/profile/send-otp-email/', views.send_otp_email, name='send_otp_email'),
    path('seller/profile/verify-otp-email/', views.verify_otp_email, name='verify_otp_email'),
    path('seller/profile/send-otp-phone/', views.send_otp_phone, name='send_otp_phone'),
    path('seller/profile/verify-otp-phone/', views.verify_otp_phone, name='verify_otp_phone'),
]
