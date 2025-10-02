from django.contrib import admin

from .models import Project, ProjectGroup, Schema, ProjectSchema


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


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("schema_id", "name", "category", "is_locked", "usage_count", "extraction_count", "created_at")
    list_filter = ("is_locked", "category", "created_at")
    search_fields = ("schema_id", "name", "name_zh", "description")
    readonly_fields = ("schema_id", "created_at", "updated_at", "locked_at", "usage_count", "extraction_count")
    ordering = ("-updated_at",)
    
    fieldsets = (
        ('基本信息', {
            'fields': ('schema_id', 'name', 'name_zh', 'description', 'category', 'version')
        }),
        ('Schema 定义', {
            'fields': ('fields_definition',),
            'classes': ('wide',),
        }),
        ('状态和统计', {
            'fields': ('is_locked', 'locked_at', 'usage_count', 'extraction_count')
        }),
        ('版本追踪', {
            'fields': ('parent_schema',)
        }),
        ('时间戳', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        if obj and not obj.can_delete():
            return False
        return super().has_delete_permission(request, obj)


@admin.register(ProjectSchema)
class ProjectSchemaAdmin(admin.ModelAdmin):
    list_display = ("project", "schema", "is_active", "display_order", "added_at")
    list_filter = ("is_active", "added_at")
    search_fields = ("project__name", "schema__name")
    ordering = ("project", "display_order")
