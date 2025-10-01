from django.contrib import admin

from .models import Paper


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = ("paper_id", "project", "title", "updated_at")
    search_fields = ("paper_id", "title", "project__project_id")
    ordering = ("-updated_at", "paper_id")
