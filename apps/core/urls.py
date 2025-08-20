"""
تكوين URLs لتطبيق core الرئيسي
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # الصفحة الرئيسية
    path('', views.home, name='home'),
    
    # صفحات المحافظات
    path('governorates/', views.governorates, name='governorates'),
    path('governorate/<slug:governorate_slug>/', views.governorate_detail, name='governorate_detail'),
    
    # صفحات عامة
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    
    # API endpoints
    path('api/governorates/search/', views.api_governorates_search, name='api_governorates_search'),
    path("api/candidates/search/", views.api_candidates_search, name="api_candidates_search"),
    path("profile/", views.profile_view, name="profile"),

    path("logout/", views.logout_view, name="logout"),

]