from django.contrib import admin

from .models import Project, ProjectGroup


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("project_id", "name", "model", "updated_at")
    search_fields = ("project_id", "name", "model")
    ordering = ("-updated_at",)


@admin.register(ProjectGroup)
class ProjectGroupAdmin(admin.ModelAdmin):
    list_display = ("project", "group_name", "updated_at")
    search_fields = ("project__project_id", "group_name")
    ordering = ("project__project_id", "group_name")
