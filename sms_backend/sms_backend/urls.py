'''
URL Configuration for SMS Backend
'''

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('projects/', include('projects.urls')),
    path('papers/', include('papers.urls')),
    path('extractions/', include('extractions.urls')),
    path('agents/', include('agents.urls')),  # AI Agent system
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
