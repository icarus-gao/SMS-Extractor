from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/projects/", include("projects.urls")),
    path("api/papers/", include("papers.urls")),
    path("api/extractions/", include("extractions.urls")),
]
