"""
URLs for news app
"""

from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    # News display
    path('', views.news_list, name='news_list'),
    path('<int:pk>/', views.news_detail, name='news_detail'),
    
    # API endpoints
    path('api/ticker/', views.api_ticker_news, name='api_ticker_news'),
]

