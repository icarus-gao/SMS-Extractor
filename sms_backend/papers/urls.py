from django.urls import path

from .views import (
    PaperLibraryView,
    PaperUploadView,
    PaperDetailView,
    PaperUpdateView,
    PaperDeleteView,
    PaperPDFView,
    BibTeXImportView,
    PaperListAPIView,
    PaperDetailAPIView,
)

app_name = 'papers'

urlpatterns = [
    # Main paper library views
    path('', PaperLibraryView.as_view(), name='library'),
    path('upload/', PaperUploadView.as_view(), name='upload'),
    path('import/', BibTeXImportView.as_view(), name='import'),
    path('<str:paper_id>/', PaperDetailView.as_view(), name='detail'),
    path('<str:paper_id>/edit/', PaperUpdateView.as_view(), name='edit'),
    path('<str:paper_id>/delete/', PaperDeleteView.as_view(), name='delete'),
    path('<str:paper_id>/pdf/', PaperPDFView.as_view(), name='pdf'),
    
    # Legacy API endpoints
    path('api/list/', PaperListAPIView.as_view(), name='api-list'),
    path('api/<str:paper_id>/', PaperDetailAPIView.as_view(), name='api-detail'),
]
