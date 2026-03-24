from django.urls import path
from management import views

urlpatterns = [
    path('api/wallet-transaction/', views.wallet_transaction_api, name='wallet_transaction_api'),
]
