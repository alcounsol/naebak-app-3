"""
تكوين URLs لتطبيق naebak الرئيسي
"""

from django.urls import path
from . import views

app_name = 'naebak'

urlpatterns = [
    # الصفحة الرئيسية
    path('', views.home, name='home'),
    
    # صفحات المحافظات
    path('governorates/', views.governorates, name='governorates'),
    path('governorate/<slug:slug>/', views.governorate_detail, name='governorate_detail'),
    path('governorate/<slug:slug>/candidates/', views.governorate_candidates_list, name='governorate_candidates_list'),
    
    # صفحات المرشحين
    path('candidates/', views.candidates, name='candidates'),
    path('candidate/<int:pk>/', views.candidate_detail, name='candidate_detail'),
    path('candidate-profile/', views.candidate_profile, name='candidate_profile'),
    
    # صفحات المواطنين
    path('register/', views.citizen_register, name='register'),
    path("profile/", views.citizen_profile, name="profile"),
    path('conversations/', views.conversations, name='conversations'),
    path('my-messages/', views.my_messages, name='my_messages'),
    path('message-thread/<int:message_id>/', views.message_thread, name='message_thread'),
    path('send-message/<int:candidate_id>/', views.send_message_to_candidate, name='send_message_to_candidate'),
    
    # Notification API endpoints
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/notifications/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # صفحات الإدارة
    path("admin-panel/users/", views.user_management, name="user_management"),
    path("admin-panel/", views.admin_panel, name="admin_panel"),
    path("admin-panel/backup/", views.backup_data, name="backup_data"),
    path("admin-panel/restore/", views.restore_data, name="restore_data"),
    path("admin-panel/create-candidate/", views.create_candidate, name="create_candidate"),
    path("admin-panel/manage-candidates/", views.manage_candidates, name="manage_candidates"),
    path("admin-panel/delete-candidate/<int:candidate_id>/", views.delete_candidate, name="delete_candidate"),
    
    # Development helper (should be removed in production)
    path('create-governorates/', views.create_governorates_data, name='create_governorates'),
    
    # تسجيل الدخول والخروج
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Candidate Dashboard URLs
    path('candidate/dashboard/', views.candidate_dashboard, name='candidate_dashboard'),
    path('candidate/profile-edit/', views.candidate_profile_edit, name='candidate_profile_edit'),
    path('candidate/electoral-program/', views.candidate_electoral_program, name='candidate_electoral_program'),
    path('candidate/promises/', views.candidate_promises, name='candidate_promises'),
    path('candidate/messages/', views.candidate_messages, name='candidate_messages'),
    path('candidate/message-reply/<int:message_id>/', views.candidate_message_reply, name='candidate_message_reply'),
    path('candidate/ratings-votes/', views.candidate_ratings_votes, name='candidate_ratings_votes'),
    path('candidate/delete-promise/<int:promise_id>/', views.delete_promise, name='delete_promise'),
    
    # News Management URLs
    path('admin-panel/news/', views.news_management, name='news_management'),
    path('admin-panel/news/create/', views.create_news, name='create_news'),
    path('admin-panel/news/edit/<int:news_id>/', views.edit_news, name='edit_news'),
    path('admin-panel/news/delete/<int:news_id>/', views.delete_news, name='delete_news'),
    path('admin-panel/news/toggle-status/<int:news_id>/', views.toggle_news_status, name='toggle_news_status'),
    path('api/ticker-news/', views.get_ticker_news, name='get_ticker_news'),
    path('news/<int:news_id>/', views.news_detail, name='news_detail'),
    
    # Activity Monitoring URLs
    path('admin-panel/activity/', views.activity_monitoring, name='activity_monitoring'),
    path('admin-panel/activity/<int:activity_id>/', views.activity_detail, name='activity_detail'),
    path('admin-panel/user-activity/<int:user_id>/', views.user_activity_history, name='user_activity_history'),
    path('api/activity-stats/', views.get_activity_stats_api, name='get_activity_stats_api'),
    
    # Reports and Statistics URLs
    path('admin-panel/reports/', views.reports_dashboard, name='reports_dashboard'),
    path('admin-panel/reports/candidates/', views.candidate_performance_report, name='candidate_performance_report'),
    path('admin-panel/reports/engagement/', views.user_engagement_report, name='user_engagement_report'),
    path('admin-panel/reports/export/<str:report_type>/', views.export_report_csv, name='export_report_csv'),
    path('api/chart-data/', views.get_chart_data_api, name='get_chart_data_api'),
    
    # Legal Pages
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    
    # ملف robots.txt
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path("candidate/<int:pk>/rate/", views.rate_candidate, name="rate_candidate"),
    path("candidate/<int:pk>/vote/", views.vote_candidate, name="vote_candidate"),
]