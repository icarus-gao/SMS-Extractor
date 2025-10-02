"""
Django models for AI Agent system
"""

from django.db import models
from django.contrib.auth.models import User
from projects.models import Project
from papers.models import Paper
from extractions.models import Extraction
import json


class AgentConversation(models.Model):
    """Store conversation history with AI agents"""
    
    AGENT_TYPES = [
        ('extraction', 'Extraction Agent'),
        ('conversation', 'Conversation Agent'),
        ('workflow', 'Workflow Agent'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='agent_conversations', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agent_conversations', null=True, blank=True)
    agent_type = models.CharField(max_length=50, choices=AGENT_TYPES)
    session_id = models.CharField(max_length=100, db_index=True)
    
    # Conversation data
    messages = models.JSONField(default=list, help_text="List of messages in the conversation")
    context = models.JSONField(default=dict, help_text="Additional context for the conversation")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['session_id', 'agent_type']),
            models.Index(fields=['project', 'agent_type']),
        ]
    
    def __str__(self):
        return f"{self.agent_type} - Session {self.session_id}"
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation"""
        from datetime import datetime
        self.messages.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        self.save()
    
    def get_history(self, limit: int = 10):
        """Get recent conversation history"""
        return self.messages[-limit:] if self.messages else []


class AgentTask(models.Model):
    """Track agent tasks and their execution"""
    
    TASK_STATUS = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    TASK_TYPES = [
        ('extraction', 'Feature Extraction'),
        ('analysis', 'Data Analysis'),
        ('batch_processing', 'Batch Processing'),
        ('quality_check', 'Quality Check'),
        ('report_generation', 'Report Generation'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='agent_tasks')
    task_type = models.CharField(max_length=50, choices=TASK_TYPES)
    status = models.CharField(max_length=20, choices=TASK_STATUS, default='pending')
    
    # Task configuration
    config = models.JSONField(default=dict, help_text="Task configuration parameters")
    input_data = models.JSONField(default=dict, help_text="Input data for the task")
    
    # Results
    result = models.JSONField(default=dict, help_text="Task execution results")
    error_message = models.TextField(blank=True, help_text="Error message if task failed")
    
    # Progress tracking
    progress = models.IntegerField(default=0, help_text="Progress percentage (0-100)")
    total_items = models.IntegerField(default=0)
    processed_items = models.IntegerField(default=0)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Relationships
    related_papers = models.ManyToManyField(Paper, blank=True, related_name='agent_tasks')
    related_extractions = models.ManyToManyField(Extraction, blank=True, related_name='agent_tasks')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['task_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.get_task_type_display()} - {self.get_status_display()}"
    
    def update_progress(self, processed: int):
        """Update task progress"""
        self.processed_items = processed
        if self.total_items > 0:
            self.progress = int((processed / self.total_items) * 100)
        self.save()


class AgentRecommendation(models.Model):
    """Store agent recommendations and suggestions"""
    
    RECOMMENDATION_TYPES = [
        ('field_suggestion', 'Field Suggestion'),
        ('workflow_optimization', 'Workflow Optimization'),
        ('quality_improvement', 'Quality Improvement'),
        ('next_action', 'Next Action'),
        ('insight', 'Data Insight'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='agent_recommendations')
    recommendation_type = models.CharField(max_length=50, choices=RECOMMENDATION_TYPES)
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='medium')
    
    # Content
    title = models.CharField(max_length=255)
    description = models.TextField()
    suggested_action = models.JSONField(default=dict, help_text="Suggested action details")
    
    # Status
    is_applied = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    applied_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by_agent = models.CharField(max_length=50)
    
    class Meta:
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['project', 'is_applied']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_priority_display()})"
