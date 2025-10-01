from django.http import JsonResponse
from django.views import View

from .models import Extraction


class ExtractionListView(View):
    def get(self, request):
        qs = Extraction.objects.all().values(
            "id",
            "paper_id",
            "project_id",
            "profile",
            "model",
            "status",
            "created_at",
        )
        return JsonResponse({"extractions": list(qs)})


class ExtractionDetailView(View):
    def get(self, request, extraction_id: int):
        try:
            extraction = Extraction.objects.get(pk=extraction_id)
        except Extraction.DoesNotExist:
            return JsonResponse({"error": "Extraction not found"}, status=404)

        data = {
            "id": extraction.id,
            "paper_id": extraction.paper_id,
            "project_id": extraction.project_id,
            "profile": extraction.profile,
            "model": extraction.model,
            "status": extraction.status,
            "result_json": extraction.result_json,
            "error_msg": extraction.error_msg,
            "created_at": extraction.created_at,
        }
        return JsonResponse(data)
