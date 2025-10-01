from django.urls import path

from .views import PaperListView, PaperDetailView

urlpatterns = [
    path("", PaperListView.as_view(), name="paper-list"),
    path("<str:paper_id>/", PaperDetailView.as_view(), name="paper-detail"),
]
