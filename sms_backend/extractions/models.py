from django.db import models

from projects.models import Project
from papers.models import Paper


class Extraction(models.Model):
    id = models.AutoField(primary_key=True)
    paper = models.ForeignKey(Paper, related_name="extractions", on_delete=models.CASCADE)
    project = models.ForeignKey(Project, related_name="extractions", on_delete=models.CASCADE, blank=True, null=True)
    profile = models.CharField(max_length=255, blank=True, null=True)
    codebook_path = models.TextField(blank=True, null=True)
    model = models.CharField(max_length=255)
    base_url = models.TextField(blank=True, null=True)
    mock = models.BooleanField(default=False)
    prompt_tokens = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=64)
    result_json = models.TextField(blank=True, null=True)
    error_msg = models.TextField(blank=True, null=True)
    batch_id = models.CharField(max_length=255, blank=True, null=True)
    part_index = models.IntegerField(blank=True, null=True)
    part_total = models.IntegerField(blank=True, null=True)
    created_at = models.BigIntegerField(blank=True, null=True)

    class Meta:
        db_table = "extractions"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Extraction #{self.id} ({self.status})"
