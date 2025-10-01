from django.http import JsonResponse
from django.views import View

from .models import Project, ProjectGroup


class ProjectListView(View):
    def get(self, request):
        projects = Project.objects.all().values(
            "project_id",
            "name",
            "model",
            "created_at",
            "updated_at",
        )
        return JsonResponse({"projects": list(projects)})


class ProjectDetailView(View):
    def get(self, request, project_id: str):
        try:
            project = Project.objects.get(project_id=project_id)
        except Project.DoesNotExist:
            return JsonResponse({"error": "Project not found"}, status=404)

        groups = ProjectGroup.objects.filter(project=project).values(
            "group_name", "description", "codebook_path", "prompt_path", "updated_at"
        )
        data = {
            "project_id": project.project_id,
            "name": project.name,
            "model": project.model,
            "notes": project.notes,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "feature_groups": list(groups),
        }
        return JsonResponse(data)
