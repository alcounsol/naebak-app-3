"""
URLs for accounts app
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.citizen_register, name='citizen_register'),
    
    # Profile management
    path('profile/', views.citizen_profile, name='citizen_profile'),
    path('profile/edit/', views.edit_citizen_profile, name='edit_citizen_profile'),
    path("quick-login/", views.quick_login, name="quick_login"),
]
