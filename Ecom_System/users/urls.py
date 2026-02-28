from django.urls import path
from . import views

urlpatterns = [
    path('profile/edit/', views.staff_profile_edit, name='staff_profile_edit'),
]
