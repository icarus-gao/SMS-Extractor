"""
Views for AI Agent system
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json
import uuid
from datetime import datetime

from projects.models import Project
from papers.models import Paper
from .models import AgentConversation, AgentTask, AgentRecommendation
import sys
sys.path.insert(0, '/Users/gaoxiangyu/Desktop/sms_extractor/sms_backend')
from ai_agents import AgentOrchestrator


# Initialize agent orchestrator
orchestrator = AgentOrchestrator()


# ============================================================================
# Agent Chat Interface
# ============================================================================

def agent_chat(request, project_id=None):
    """Main chat interface for AI agents"""
    project = None
    if project_id:
        project = get_object_or_404(Project, project_id=project_id)
    
    # Get recent conversations
    if project:
        conversations = AgentConversation.objects.filter(
            project=project, 
            is_active=True
        )[:5]
    else:
        conversations = AgentConversation.objects.filter(is_active=True)[:5]
    
    context = {
        'project': project,
        'conversations': conversations,
        'agent_types': [
            {'value': 'conversation', 'label': 'Research Assistant', 'icon': 'chat-dots'},
            {'value': 'extraction', 'label': 'Extraction Agent', 'icon': 'file-earmark-text'},
            {'value': 'workflow', 'label': 'Workflow Agent', 'icon': 'diagram-3'},
        ]
    }
    
    return render(request, 'agents/chat.html', context)


@require_http_methods(["POST"])
@csrf_exempt
def agent_send_message(request):
    """Send a message to an agent"""
    try:
        data = json.loads(request.body)
        
        agent_type = data.get('agent_type', 'conversation')
        message = data.get('message', '')
        project_id = data.get('project_id')
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Get or create conversation
        conversation, created = AgentConversation.objects.get_or_create(
            session_id=session_id,
            agent_type=agent_type,
            defaults={'project_id': project_id if project_id else None}
        )
        
        # Add user message
        conversation.add_message('user', message)
        
        # Get project context if available
        context = {}
        if project_id:
            project = Project.objects.get(project_id=project_id)
            context = {
                'project_name': project.name,
                'project_id': project.project_id,
                'paper_count': Paper.objects.filter(project=project).count(),
            }
        
        # Get agent response
        response = orchestrator.chat_with_agent(agent_type, message, context=context)
        
        # Add assistant message
        conversation.add_message('assistant', response)
        
        return JsonResponse({
            'success': True,
            'response': response,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def agent_conversation_history(request, session_id):
    """Get conversation history"""
    try:
        conversation = AgentConversation.objects.get(session_id=session_id)
        
        return JsonResponse({
            'success': True,
            'messages': conversation.messages,
            'agent_type': conversation.agent_type,
            'created_at': conversation.created_at.isoformat()
        })
        
    except AgentConversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)


# Agent Recommendations
def agent_recommendations(request, project_id):
    """View agent recommendations for a project"""
    project = get_object_or_404(Project, project_id=project_id)
    recommendations = AgentRecommendation.objects.filter(
        project=project,
        is_dismissed=False
    )
    
    context = {
        'project': project,
        'recommendations': recommendations,
    }
    
    return render(request, 'agents/recommendations.html', context)
