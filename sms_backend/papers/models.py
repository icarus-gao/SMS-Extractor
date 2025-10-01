from django.db import models

from projects.models import Project


class Paper(models.Model):
    paper_id = models.CharField(max_length=255, primary_key=True)
    project = models.ForeignKey(Project, related_name="papers", on_delete=models.CASCADE, blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    citation = models.TextField(blank=True, null=True)
    citation_format = models.CharField(max_length=64, blank=True, null=True)
    pdf_sha256 = models.CharField(max_length=128, blank=True, null=True)
    pdf_path = models.TextField(blank=True, null=True)
    created_at = models.BigIntegerField(blank=True, null=True)
    updated_at = models.BigIntegerField(blank=True, null=True)

    class Meta:
        db_table = "papers"
        ordering = ["-updated_at", "paper_id"]

    def __str__(self) -> str:
        return self.paper_id
