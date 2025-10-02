from django.urls import path

from .views import (
    ProjectListView, 
    ProjectDetailView,
    ProjectListHTMLView,
    ProjectDetailHTMLView,
    AddPaperToProjectView,
    RemovePaperFromProjectView,
    UpdateProjectSettingsView,
    UploadPaperToProjectView,
)

app_name = 'projects'

urlpatterns = [
    # API endpoints (keep for backward compatibility)
    path("api/", ProjectListView.as_view(), name="project-list-api"),
    path("api/<str:project_id>/", ProjectDetailView.as_view(), name="project-detail-api"),
    
    # HTML views
    path("", ProjectListHTMLView.as_view(), name="list"),
    path("<str:project_id>/", ProjectDetailHTMLView.as_view(), name="detail"),
    path("<str:project_id>/add-paper/", AddPaperToProjectView.as_view(), name="add-paper"),
    path("<str:project_id>/remove-paper/<str:paper_id>/", RemovePaperFromProjectView.as_view(), name="remove-paper"),
    path("<str:project_id>/settings/", UpdateProjectSettingsView.as_view(), name="update-settings"),
    path("<str:project_id>/upload-paper/", UploadPaperToProjectView.as_view(), name="upload-paper"),
]
