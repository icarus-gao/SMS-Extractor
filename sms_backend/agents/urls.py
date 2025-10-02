"""
URLs for AI Agent system
"""

from django.urls import path
from . import views

app_name = 'agents'

urlpatterns = [
    # Chat interface
    path('chat/', views.agent_chat, name='chat'),
    path('chat/<str:project_id>/', views.agent_chat, name='project-chat'),
    path('api/send-message/', views.agent_send_message, name='send-message'),
    path('api/conversation/<str:session_id>/', views.agent_conversation_history, name='conversation-history'),
    
    # Recommendations
    path('recommendations/<str:project_id>/', views.agent_recommendations, name='recommendations'),
]
