from django.db import models
from django.utils import timezone
import json
import uuid


class Schema(models.Model):
    """Schema 定义 - 用于结构化数据提取的模板"""
    
    schema_id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    name_zh = models.CharField(max_length=255, blank=True, null=True, verbose_name="中文名称")
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True, verbose_name="分类")
    
    # Schema 的核心：字段定义（JSON 格式）
    fields_definition = models.TextField(help_text="JSON format schema definition")
    
    # 不可变性控制
    is_locked = models.BooleanField(default=False, help_text="锁定后不可编辑")
    locked_at = models.DateTimeField(blank=True, null=True)
    
    # 版本追踪（复制时使用）
    parent_schema = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='children',
        help_text="从哪个 Schema 复制而来"
    )
    version = models.CharField(max_length=50, default="1.0")
    
    # 使用统计
    usage_count = models.IntegerField(default=0, help_text="被多少个项目使用")
    extraction_count = models.IntegerField(default=0, help_text="总共提取了多少次")
    
    # 创建者和时间
    created_by = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "schemas"
        ordering = ["-updated_at", "schema_id"]
    
    def __str__(self):
        status = "🔒 Locked" if self.is_locked else "📝 Draft"
        return f"{self.name} ({self.schema_id}) - {status}"
    
    def save(self, *args, **kwargs):
        # 新建时自动生成 schema_id
        if not self.schema_id:
            self.schema_id = self.generate_schema_id()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_schema_id():
        """生成唯一的 schema_id"""
        return f"schema_{uuid.uuid4().hex[:12]}"
    
    def lock(self):
        """锁定 Schema（首次使用时调用）"""
        if not self.is_locked:
            self.is_locked = True
            self.locked_at = timezone.now()
            self.save()
    
    def can_edit(self):
        """是否可以编辑"""
        return not self.is_locked
    
    def can_delete(self):
        """是否可以删除"""
        return not self.is_locked and self.usage_count == 0
    
    def duplicate(self, new_name=None, created_by=None):
        """复制一个新的 Schema（用于演进）"""
        new_schema = Schema(
            name=new_name or f"{self.name} (Copy)",
            name_zh=self.name_zh,
            description=self.description,
            category=self.category,
            fields_definition=self.fields_definition,
            parent_schema=self,
            version=self._increment_version(),
            created_by=created_by or self.created_by,
        )
        new_schema.save()
        return new_schema
    
    def _increment_version(self):
        """版本号递增"""
        try:
            major, minor = self.version.split('.')
            return f"{major}.{int(minor) + 1}"
        except:
            return "1.1"
    
    def get_fields(self):
        """获取字段定义（解析 JSON）"""
        try:
            schema_def = json.loads(self.fields_definition)
            return schema_def.get('fields', [])
        except:
            return []
    
    def get_export_fields(self):
        """获取需要导出的字段"""
        fields = self.get_fields()
        return [f for f in fields if f.get('export', {}).get('enabled', True)]
    
    def increment_usage(self):
        """增加使用计数"""
        self.usage_count += 1
        self.save()
    
    def increment_extraction(self):
        """增加提取计数"""
        self.extraction_count += 1
        self.save()


class ProjectSchema(models.Model):
    """项目和 Schema 的多对多关联"""
    
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(
        'Project', 
        on_delete=models.CASCADE, 
        related_name='project_schemas'
    )
    schema = models.ForeignKey(
        Schema, 
        on_delete=models.CASCADE, 
        related_name='project_associations'
    )
    
    # 关联时的配置
    display_order = models.IntegerField(default=0, help_text="显示顺序")
    is_active = models.BooleanField(default=True, help_text="是否启用")
    
    # 时间戳
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "project_schemas"
        unique_together = ('project', 'schema')
        ordering = ['project', 'display_order', '-added_at']
    
    def __str__(self):
        return f"{self.project.name} - {self.schema.name}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # 首次关联时，锁定 Schema 并增加使用计数
        if is_new and not self.schema.is_locked:
            self.schema.lock()
            self.schema.increment_usage()


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
