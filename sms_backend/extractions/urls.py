from django.urls import path

from .views import ExtractionListView, ExtractionDetailView

urlpatterns = [
    path("", ExtractionListView.as_view(), name="extraction-list"),
    path("<int:extraction_id>/", ExtractionDetailView.as_view(), name="extraction-detail"),
]
