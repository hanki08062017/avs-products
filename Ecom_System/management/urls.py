from django.urls import path
from management import views

urlpatterns = [
    path('api/wallet-transaction/', views.wallet_transaction_api, name='wallet_transaction_api'),
    path('management/login/', views.mgmt_login, name='mgmt_login'),
    path('management/logout/', views.mgmt_logout, name='mgmt_logout'),
    path('management/', views.mgmt_dashboard, name='mgmt_dashboard'),
    path('management/wallet/import/', views.mgmt_wallet_import, name='mgmt_wallet_import'),
    path('management/<str:table>/add/', views.mgmt_add, name='mgmt_add'),
    path('management/<str:table>/<str:pk>/edit/', views.mgmt_edit, name='mgmt_edit'),
    path('management/<str:table>/<str:pk>/delete/', views.mgmt_delete, name='mgmt_delete'),
    path('management/<str:table>/', views.mgmt_table, name='mgmt_table'),
]
