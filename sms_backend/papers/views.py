from django.http import JsonResponse
from django.views import View

from .models import Paper


class PaperListView(View):
    def get(self, request):
        qs = Paper.objects.all().values(
            "paper_id",
            "project_id",
            "title",
            "citation_format",
            "updated_at",
        )
        return JsonResponse({"papers": list(qs)})


class PaperDetailView(View):
    def get(self, request, paper_id: str):
        try:
            paper = Paper.objects.get(paper_id=paper_id)
        except Paper.DoesNotExist:
            return JsonResponse({"error": "Paper not found"}, status=404)

        data = {
            "paper_id": paper.paper_id,
            "project_id": paper.project_id,
            "title": paper.title,
            "citation": paper.citation,
            "citation_format": paper.citation_format,
            "pdf_path": paper.pdf_path,
            "created_at": paper.created_at,
            "updated_at": paper.updated_at,
        }
        return JsonResponse(data)
