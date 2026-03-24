from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.customer_login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.customer_logout_view, name='logout'),
    path('product/<str:product_id>/', views.product_detail, name='product_detail'),
    path('checkout/', views.checkout, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('<str:username>/profile/', views.profile_view, name='profile'),
    path('confirm-order/', views.confirm_order, name='confirm_order'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('orders/', views.order_history, name='order_history'),
    path('wallet/', views.wallet_view, name='wallet'),
    path('payment-history/', views.payment_history, name='payment_history'),
    path('view-invoice/<str:order_id>/', views.download_invoice, name='download_invoice'),
    path('get-delivery-data/', views.get_delivery_data, name='get_delivery_data'),
    path('update-address/', views.update_address, name='update_address'),
    path('set-default-address/', views.set_default_address, name='set_default_address'),
    path('delete-address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('edit-address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('change-password/', views.change_password, name='change_password'),
    path('check-username/', views.check_username, name='check_username'),
]
