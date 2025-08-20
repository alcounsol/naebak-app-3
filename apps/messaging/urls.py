"""
URLs for messaging app
"""

from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Message management
    path('send/<int:candidate_id>/', views.send_message, name='send_message'),
    path('inbox/', views.message_inbox, name='message_inbox'),
    path('thread/<int:message_id>/', views.message_thread, name='message_thread'),
    path('reply/<int:message_id>/', views.reply_message, name='reply_message'),
]

