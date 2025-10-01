from django.contrib import admin

from .models import Extraction


@admin.register(Extraction)
class ExtractionAdmin(admin.ModelAdmin):
    list_display = ("id", "paper", "project", "status", "created_at")
    search_fields = ("paper__paper_id", "project__project_id", "status")
    ordering = ("-created_at", "paper__paper_id")
