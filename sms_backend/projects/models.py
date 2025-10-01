from django.db import models


class Project(models.Model):
    project_id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    codebook_path = models.TextField(blank=True, null=True)
    template_path = models.TextField(blank=True, null=True)
    model = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.BigIntegerField(blank=True, null=True)
    updated_at = models.BigIntegerField(blank=True, null=True)

    class Meta:
        db_table = "projects"
        ordering = ["-updated_at", "project_id"]

    def __str__(self) -> str:
        return f"{self.name} ({self.project_id})"


class ProjectGroup(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, related_name="feature_groups", on_delete=models.CASCADE)
    group_name = models.CharField(max_length=255)
    fields_json = models.TextField()
    codebook_path = models.TextField(blank=True, null=True)
    prompt_path = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.BigIntegerField(blank=True, null=True)
    updated_at = models.BigIntegerField(blank=True, null=True)

    class Meta:
        db_table = "project_groups"
        unique_together = ("project", "group_name")
        ordering = ["project", "group_name"]

    def __str__(self) -> str:
        return f"{self.project_id}:{self.group_name}"

    @property
    def project_id(self) -> str:
        return self.project.project_id
