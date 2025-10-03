from django.urls import path

from .views import (
    ExtractionListView, 
    ExtractionDetailView,
    run_extraction,
    extraction_detail,
    extraction_edit,
    extraction_delete,
    extraction_verify,
)

app_name = 'extractions'

urlpatterns = [
    # API endpoints (backward compatibility)
    path("api/", ExtractionListView.as_view(), name="extraction-list-api"),
    path("api/<int:extraction_id>/", ExtractionDetailView.as_view(), name="extraction-detail-api"),
    
    # HTML views
    path("<int:extraction_id>/", extraction_detail, name="detail"),
    path("<int:extraction_id>/edit/", extraction_edit, name="edit"),
    path("<int:extraction_id>/delete/", extraction_delete, name="delete"),
    path("<int:extraction_id>/verify/", extraction_verify, name="verify"),
    
    # Run extraction (project-based)
    path("run/<str:project_id>/", run_extraction, name="run"),
]
