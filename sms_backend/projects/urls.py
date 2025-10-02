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

# Schema views
from .schema_views import (
    schema_library,
    schema_detail,
    schema_create,
    schema_edit,
    schema_delete,
    schema_duplicate,
    schema_lock,
    schema_fields_api,
    schema_validate_api,
    project_add_schema,
    project_remove_schema,
)

app_name = 'projects'

urlpatterns = [
    # API endpoints (keep for backward compatibility)
    path("api/", ProjectListView.as_view(), name="project-list-api"),
    path("api/<str:project_id>/", ProjectDetailView.as_view(), name="project-detail-api"),
    
    # HTML views - Projects
    path("", ProjectListHTMLView.as_view(), name="list"),
    path("<str:project_id>/", ProjectDetailHTMLView.as_view(), name="detail"),
    path("<str:project_id>/add-paper/", AddPaperToProjectView.as_view(), name="add-paper"),
    path("<str:project_id>/remove-paper/<str:paper_id>/", RemovePaperFromProjectView.as_view(), name="remove-paper"),
    path("<str:project_id>/settings/", UpdateProjectSettingsView.as_view(), name="update-settings"),
    path("<str:project_id>/upload-paper/", UploadPaperToProjectView.as_view(), name="upload-paper"),
    
    # Schema Library URLs
    path("schemas/", schema_library, name="schema_library"),
    path("schemas/create/", schema_create, name="schema_create"),
    path("schemas/<str:schema_id>/", schema_detail, name="schema_detail"),
    path("schemas/<str:schema_id>/edit/", schema_edit, name="schema_edit"),
    path("schemas/<str:schema_id>/delete/", schema_delete, name="schema_delete"),
    path("schemas/<str:schema_id>/duplicate/", schema_duplicate, name="schema_duplicate"),
    path("schemas/<str:schema_id>/lock/", schema_lock, name="schema_lock"),
    
    # Schema API URLs
    path("api/schemas/<str:schema_id>/fields/", schema_fields_api, name="schema_fields_api"),
    path("api/schemas/validate/", schema_validate_api, name="schema_validate_api"),
    
    # Project-Schema Association URLs
    path("<str:project_id>/add-schema/", project_add_schema, name="project_add_schema"),
    path("<str:project_id>/remove-schema/<str:schema_id>/", project_remove_schema, name="project_remove_schema"),
]
