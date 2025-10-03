from django.urls import path

from .views import (
    PaperLibraryView,
    PaperUploadView,
    PaperDetailView,
    PaperUpdateView,
    PaperDeleteView,
    PaperPDFView,
    PaperUploadPDFView,
    PaperUpdateMetadataView,
    BibTeXImportView,
    BibTeXExportView,
    PaperListAPIView,
    PaperDetailAPIView,
)

app_name = 'papers'

urlpatterns = [
    # Main paper library views
    path('', PaperLibraryView.as_view(), name='library'),
    path('upload/', PaperUploadView.as_view(), name='upload'),
    path('import/', BibTeXImportView.as_view(), name='import'),
    path('export/bibtex/', BibTeXExportView.as_view(), name='export-bibtex'),
    path('<str:paper_id>/', PaperDetailView.as_view(), name='detail'),
    path('<str:paper_id>/edit/', PaperUpdateView.as_view(), name='edit'),
    path('<str:paper_id>/delete/', PaperDeleteView.as_view(), name='delete'),
    path('<str:paper_id>/pdf/', PaperPDFView.as_view(), name='pdf'),
    path('<str:paper_id>/upload-pdf/', PaperUploadPDFView.as_view(), name='upload-pdf'),
    path('<str:paper_id>/update-metadata/', PaperUpdateMetadataView.as_view(), name='update-metadata'),
    
    # Legacy API endpoints
    path('api/list/', PaperListAPIView.as_view(), name='api-list'),
    path('api/<str:paper_id>/', PaperDetailAPIView.as_view(), name='api-detail'),
]
