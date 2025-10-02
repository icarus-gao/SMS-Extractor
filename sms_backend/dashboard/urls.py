'''
URL Configuration for Dashboard App
'''

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Projects
    path('projects/', views.project_list, name='project-list'),
    path('projects/create/', views.project_create, name='project-create'),
    path('projects/<str:project_id>/', views.project_detail, name='project-detail'),
    path('projects/<str:project_id>/update/', views.project_update, name='project-update'),
    path('projects/<str:project_id>/delete/', views.project_delete, name='project-delete'),
    
    # Papers
    path('projects/<str:project_id>/papers/', views.paper_list, name='paper-list'),
    path('projects/<str:project_id>/papers/upload/', views.paper_upload, name='paper-upload'),
    path('projects/<str:project_id>/papers/<str:paper_id>/delete/', views.paper_delete, name='paper-delete'),
    
    # Feature Groups
    path('projects/<str:project_id>/groups/create/', views.group_create, name='group-create'),
    path('projects/<str:project_id>/groups/<int:group_id>/update/', views.group_update, name='group-update'),
    path('projects/<str:project_id>/groups/<int:group_id>/delete/', views.group_delete, name='group-delete'),
    
    # Extraction
    path('projects/<str:project_id>/extraction/run/', views.extraction_run, name='extraction-run'),
    path('extraction/<int:extraction_id>/', views.extraction_detail, name='extraction-detail'),
    path('extraction/<int:extraction_id>/delete/', views.extraction_delete, name='extraction-delete'),
    
    # Analytics
    path('projects/<str:project_id>/analytics/', views.project_analytics, name='project-analytics'),
    path('analytics/global/', views.global_analytics, name='global-analytics'),
]
