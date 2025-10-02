"""
Admin configuration for AI Agent system
"""

from django.contrib import admin
from .models import AgentConversation, AgentTask, AgentRecommendation


@admin.register(AgentConversation)
class AgentConversationAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'agent_type', 'project', 'is_active', 'updated_at']
    list_filter = ['agent_type', 'is_active', 'created_at']
    search_fields = ['session_id', 'project__name']
    date_hierarchy = 'created_at'


@admin.register(AgentTask)
class AgentTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'project', 'task_type', 'status', 'progress', 'created_at']
    list_filter = ['task_type', 'status', 'created_at']
    search_fields = ['project__name']
    date_hierarchy = 'created_at'


@admin.register(AgentRecommendation)
class AgentRecommendationAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'recommendation_type', 'priority', 'is_applied', 'created_at']
    list_filter = ['recommendation_type', 'priority', 'is_applied', 'is_dismissed']
    search_fields = ['title', 'description', 'project__name']
    date_hierarchy = 'created_at'
