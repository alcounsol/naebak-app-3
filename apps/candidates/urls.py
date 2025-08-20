
from django.urls import path
from . import views

app_name = 'candidates'

urlpatterns = [
    # Candidate listing and details
    path('', views.candidate_list, name='candidate_list'),
    path('<int:pk>/', views.candidate_detail, name='candidate_detail'),
    
    # Voting and rating
    path('<int:pk>/vote/', views.vote_candidate, name='vote_candidate'),
    path('<int:pk>/rate/', views.rate_candidate, name='rate_candidate'),
    
    # Candidate dashboard
    path('dashboard/', views.candidate_dashboard, name='candidate_dashboard'),
]


