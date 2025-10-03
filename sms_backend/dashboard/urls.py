'''
URL Configuration for Dashboard App
'''

from django.urls import path
from . import views

# Import schema views from projects app
from projects.schema_views import (
    schema_library,
    schema_detail,
    schema_create,
    schema_edit,
    schema_delete,
    schema_duplicate,
    schema_lock,
    schema_unlock,  # Import schema_unlock view
)

app_name = 'dashboard'

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Projects
    path('projects/', views.project_list, name='project-list'),
    path('projects/create/', views.project_create, name='project-create'),
    
    # Schema URLs (must come before the generic project_id pattern)
    path('projects/schemas/', schema_library, name='schema-library'),
    path('projects/schemas/create/', schema_create, name='schema-create'),
    path('projects/schemas/<str:schema_id>/', schema_detail, name='schema-detail'),
    path('projects/schemas/<str:schema_id>/edit/', schema_edit, name='schema-edit'),
    path('projects/schemas/<str:schema_id>/delete/', schema_delete, name='schema-delete'),
    path('projects/schemas/<str:schema_id>/duplicate/', schema_duplicate, name='schema-duplicate'),
    path('projects/schemas/<str:schema_id>/lock/', schema_lock, name='schema-lock'),
    path('projects/schemas/<str:schema_id>/unlock/', schema_unlock, name='schema-unlock'),  # Add schema_unlock URL pattern
    
    # Generic project URLs (must come after more specific patterns)
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
    
    # Analysis & Export
    path('projects/<str:project_id>/analysis/export/', views.project_analysis_export, name='analysis-export'),
    path('projects/<str:project_id>/analysis/export/<str:schema_id>/', views.project_analysis_export, name='analysis-export-schema'),
]
