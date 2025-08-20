"""
URLs for voting app
"""

from django.urls import path
from . import views

app_name = 'voting'

urlpatterns = [
    # Voting and rating views
    path('ratings/', views.rating_list, name='rating_list'),
    path('votes/', views.vote_list, name='vote_list'),
    
    # API endpoints for AJAX voting/rating
    path('api/vote/', views.api_vote, name='api_vote'),
    path('api/rate/', views.api_rate, name='api_rate'),
]

