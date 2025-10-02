from django.db import models
import json

from projects.models import Project, Schema
from papers.models import Paper


class Extraction(models.Model):
    """数据提取记录 - 对某篇论文应用 Schema 提取的结果"""
    
    id = models.AutoField(primary_key=True)
    paper = models.ForeignKey(Paper, related_name="extractions", on_delete=models.CASCADE)
    project = models.ForeignKey(Project, related_name="extractions", on_delete=models.CASCADE, blank=True, null=True)
    
    # 新增：Schema 关联
    schema = models.ForeignKey(
        Schema, 
        on_delete=models.CASCADE, 
        related_name="extractions",
        blank=True,
        null=True,
        help_text="使用的 Schema"
    )
    
    # 提取的数据（JSON 格式，包含所有字段的值、置信度、来源等）
    extracted_data = models.TextField(
        blank=True, 
        null=True,
        help_text="JSON format extracted data with confidence scores"
    )
    
    # 提取方法
    extraction_method = models.CharField(
        max_length=50,
        choices=[
            ('ai', 'AI Extraction'),
            ('manual', 'Manual Entry'),
            ('hybrid', 'AI + Manual'),
        ],
        default='ai'
    )
    
    # 旧字段（保持兼容性）
    profile = models.CharField(max_length=255, blank=True, null=True)
    codebook_path = models.TextField(blank=True, null=True)
    model = models.CharField(max_length=255, blank=True, null=True)
    base_url = models.TextField(blank=True, null=True)
    mock = models.BooleanField(default=False)
    prompt_tokens = models.IntegerField(blank=True, null=True)
    
    # 状态和结果
    status = models.CharField(
        max_length=64,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('verified', 'Verified'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    result_json = models.TextField(blank=True, null=True)  # 旧格式结果
    error_msg = models.TextField(blank=True, null=True)
    
    # 批处理相关
    batch_id = models.CharField(max_length=255, blank=True, null=True)
    part_index = models.IntegerField(blank=True, null=True)
    part_total = models.IntegerField(blank=True, null=True)
    
    # 时间戳
    created_at = models.BigIntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "extractions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['project', 'schema', 'status']),
            models.Index(fields=['paper', 'schema']),
        ]

    def __str__(self) -> str:
        schema_name = self.schema.name if self.schema else "No Schema"
        return f"Extraction #{self.id} - {schema_name} ({self.status})"
    
    def get_extracted_data(self):
        """获取提取的数据（解析 JSON）"""
        if not self.extracted_data:
            return {}
        try:
            return json.loads(self.extracted_data)
        except:
            return {}
    
    def set_extracted_data(self, data):
        """设置提取的数据"""
        self.extracted_data = json.dumps(data, ensure_ascii=False, indent=2)
    
    def get_field_value(self, field_id):
        """获取某个字段的值"""
        data = self.get_extracted_data()
        fields = data.get('fields', {})
        field_data = fields.get(field_id, {})
        return field_data.get('value')
    
    def get_field_confidence(self, field_id):
        """获取某个字段的置信度"""
        data = self.get_extracted_data()
        fields = data.get('fields', {})
        field_data = fields.get(field_id, {})
        return field_data.get('confidence', 0)
    
    def is_verified(self):
        """是否已验证"""
        return self.status == 'verified'
    
    def mark_verified(self):
        """标记为已验证"""
        self.status = 'verified'
        self.save()
