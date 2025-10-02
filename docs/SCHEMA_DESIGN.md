# Schema System Design

## 🎯 核心概念

### Schema Library 模式
- **Schema** 存储在全局 Library 中（类似 Paper Library）
- **Project** 可以关联 0 到多个 Schemas
- 每个 **Schema** 应用到 Project 的所有 Papers
- 生成 **Extractions** (Paper × Schema 的笛卡尔积)

---

## � Schema 不可变性原则

### 核心规则

**Schema 一旦被使用后即锁定，不可修改**

```
Schema 生命周期:

1. 创建阶段（Unlocked）
   ✅ 可以添加/删除/修改字段
   ✅ 可以修改 AI Prompts
   ✅ 可以删除整个 Schema
   
2. 首次使用（触发锁定）
   - Project 关联此 Schema
   - 或：首次运行 AI 提取
   → Schema 自动锁定 (is_locked = True)
   
3. 锁定阶段（Locked）
   ❌ 不可修改任何字段
   ❌ 不可删除 Schema
   ✅ 可以查看和导出
   ✅ 可以复制创建新版本
   ✅ 可以继续使用提取数据
```

### 为什么需要不可变性？

```
场景：修改 Schema 会带来的问题

假设：
- Schema v1 有字段：[Method, Dataset, Accuracy]
- 已提取 20 篇论文的数据
- 修改 Schema：删除 "Accuracy"，添加 "Training Time"

问题：
1. 已提取的 20 条数据包含 "Accuracy" 但没有 "Training Time"
2. 新提取的数据包含 "Training Time" 但没有 "Accuracy"  
3. 数据结构不一致，无法生成统一的表格
4. 导出时会出现混乱（部分行有某些列，部分没有）

解决方案：不允许修改，必须创建新版本
```

### 如何演化 Schema？

```
方法 1: 复制并修改（推荐）

操作：
1. 找到现有 Schema "ML Methods v1"
2. 点击 [Duplicate]
3. 系统创建 "ML Methods v2"（完全复制）
4. 在 v2 中修改字段
5. 保存 v2

结果：
- v1 保持不变，继续服务已有数据
- v2 是独立的新 Schema
- 可以选择：
  - 在新 Project 中使用 v2
  - 对已有 Papers 用 v2 重新提取（生成新的 Extractions）
```

```
方法 2: 从模板创建

操作：
1. 使用官方模板 "ML Methods Template"
2. 基于模板创建 "My Custom ML Analysis"
3. 添加自定义字段
4. 保存为自己的 Schema

优势：
- 标准化的基础字段
- 快速创建
- 避免重复设计
```

---

## �📊 数据库模型设计

### 1. Schema Model (全局)

```python
class Schema(models.Model):
    """
    Schema 定义 - 存储在全局 Schema Library
    类似于数据表的结构定义
    
    重要：Schema 是不可变的（Immutable）
    - 一旦被 Project 使用后，不允许修改
    - 需要修改时，必须复制创建新版本
    """
    
    # 基础信息
    schema_id = models.CharField(max_length=255, primary_key=True, unique=True)
    name = models.CharField(max_length=255, help_text="Schema 名称，如：ML Methods Comparison")
    description = models.TextField(blank=True, null=True, help_text="Schema 用途说明")
    
    # 分类和标签
    category = models.CharField(
        max_length=100, 
        blank=True, null=True,
        help_text="分类：ML, Security, IoT, Performance, General"
    )
    tags = models.TextField(blank=True, null=True, help_text="标签，JSON 数组")
    
    # Schema 定义（核心 - 不可修改）
    fields_definition = models.TextField(help_text="字段定义，JSON 格式，创建后不可修改")
    
    # 版本和继承关系
    version = models.CharField(max_length=20, default="1.0")
    parent_schema = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name="derived_schemas",
        help_text="如果是从其他 Schema 复制而来，记录父 Schema"
    )
    
    # 状态和权限
    is_locked = models.BooleanField(
        default=False, 
        help_text="是否已被使用而锁定（不可删除）"
    )
    is_public = models.BooleanField(default=True, help_text="是否公开到社区库")
    is_template = models.BooleanField(default=False, help_text="是否为官方模板")
    
    # 统计信息
    usage_count = models.IntegerField(default=0, help_text="被多少个 Project 使用")
    extraction_count = models.IntegerField(default=0, help_text="总共提取了多少条数据")
    
    # 元数据
    created_by = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.BigIntegerField(blank=True, null=True)
    
    class Meta:
        db_table = "schemas"
        ordering = ["-created_at", "name"]
        indexes = [
            models.Index(fields=['category', 'is_public']),
            models.Index(fields=['is_template']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.schema_id})"
    
    def can_delete(self):
        """检查是否可以删除（未被使用）"""
        return self.usage_count == 0 and self.extraction_count == 0
    
    def can_edit(self):
        """检查是否可以编辑（未被锁定）"""
        return not self.is_locked
    
    def lock(self):
        """锁定 Schema（首次被使用时调用）"""
        self.is_locked = True
        self.save()
```

#### fields_definition JSON 结构

```json
{
  "version": "1.0",
  "metadata": {
    "description": "用于对比不同机器学习方法",
    "use_case": "Related Work 章节的对比表格",
    "output_format": "table"
  },
  "fields": [
    {
      "id": "method_name",
      "name": "Method Name",
      "name_zh": "方法名称",
      "type": "text",
      "required": true,
      "order": 1,
      
      "description": "机器学习方法的名称",
      "placeholder": "e.g., CNN, LSTM, Transformer",
      
      "validation": {
        "max_length": 100,
        "pattern": null
      },
      
      "extraction": {
        "mode": "ai",
        "prompt": "What is the name of the machine learning method or model used in this paper? Provide the specific name (e.g., CNN, LSTM, ResNet).",
        "fallback_prompt": "What algorithm or approach is proposed in this paper?",
        "confidence_threshold": 0.7,
        "extraction_strategy": "semantic_search"
      },
      
      "display": {
        "width": 150,
        "align": "left",
        "format": null
      }
    },
    
    {
      "id": "dataset",
      "name": "Dataset",
      "name_zh": "数据集",
      "type": "text",
      "required": true,
      "order": 2,
      
      "description": "使用的数据集名称",
      "placeholder": "e.g., MNIST, ImageNet, COCO",
      
      "validation": {
        "max_length": 200
      },
      
      "extraction": {
        "mode": "ai",
        "prompt": "What dataset is used for training or evaluation? Provide the dataset name.",
        "confidence_threshold": 0.7
      },
      
      "display": {
        "width": 120,
        "align": "left"
      }
    },
    
    {
      "id": "accuracy",
      "name": "Accuracy",
      "name_zh": "准确率",
      "type": "number",
      "required": false,
      "order": 3,
      
      "description": "模型准确率（百分比）",
      "placeholder": "e.g., 98.5",
      
      "validation": {
        "min": 0,
        "max": 100,
        "decimal_places": 2
      },
      
      "unit": "%",
      
      "extraction": {
        "mode": "ai",
        "prompt": "What is the accuracy of the model? Provide a number (percentage). If multiple accuracies are reported, provide the best one.",
        "confidence_threshold": 0.6,
        "post_process": "extract_number"
      },
      
      "display": {
        "width": 80,
        "align": "right",
        "format": "0.00"
      }
    },
    
    {
      "id": "model_type",
      "name": "Model Type",
      "name_zh": "模型类型",
      "type": "select",
      "required": true,
      "order": 4,
      
      "description": "模型的类别",
      
      "options": [
        {"value": "cnn", "label": "CNN (Convolutional Neural Network)"},
        {"value": "rnn", "label": "RNN (Recurrent Neural Network)"},
        {"value": "lstm", "label": "LSTM"},
        {"value": "transformer", "label": "Transformer"},
        {"value": "gan", "label": "GAN"},
        {"value": "ensemble", "label": "Ensemble"},
        {"value": "other", "label": "Other"}
      ],
      
      "extraction": {
        "mode": "ai",
        "prompt": "What type of model is used? Choose from: CNN, RNN, LSTM, Transformer, GAN, Ensemble, or Other.",
        "confidence_threshold": 0.8,
        "post_process": "map_to_options"
      },
      
      "display": {
        "width": 120,
        "align": "left"
      }
    },
    
    {
      "id": "application_domains",
      "name": "Application Domains",
      "name_zh": "应用领域",
      "type": "multi-select",
      "required": false,
      "order": 5,
      
      "description": "模型应用的领域",
      
      "options": [
        {"value": "cv", "label": "Computer Vision"},
        {"value": "nlp", "label": "Natural Language Processing"},
        {"value": "speech", "label": "Speech Recognition"},
        {"value": "iot", "label": "IoT"},
        {"value": "healthcare", "label": "Healthcare"},
        {"value": "finance", "label": "Finance"}
      ],
      
      "extraction": {
        "mode": "ai",
        "prompt": "What application domains is this method used for? Select all that apply from: Computer Vision, NLP, Speech, IoT, Healthcare, Finance.",
        "confidence_threshold": 0.7
      },
      
      "display": {
        "width": 150,
        "align": "left",
        "format": "comma_separated"
      }
    },
    
    {
      "id": "training_time",
      "name": "Training Time",
      "name_zh": "训练时间",
      "type": "number",
      "required": false,
      "order": 6,
      
      "description": "模型训练时间",
      "placeholder": "e.g., 24",
      
      "validation": {
        "min": 0,
        "decimal_places": 2
      },
      
      "unit": "hours",
      
      "extraction": {
        "mode": "ai",
        "prompt": "How long does it take to train the model? Provide time in hours. If given in other units, convert to hours.",
        "confidence_threshold": 0.5
      },
      
      "display": {
        "width": 100,
        "align": "right",
        "format": "0.00"
      }
    },
    
    {
      "id": "hardware",
      "name": "Hardware",
      "name_zh": "硬件要求",
      "type": "text",
      "required": false,
      "order": 7,
      
      "description": "训练使用的硬件",
      "placeholder": "e.g., 4x NVIDIA V100",
      
      "extraction": {
        "mode": "ai",
        "prompt": "What hardware is used for training? Include GPU/CPU type and count.",
        "confidence_threshold": 0.6
      },
      
      "display": {
        "width": 150,
        "align": "left"
      }
    },
    
    {
      "id": "code_available",
      "name": "Code Available",
      "name_zh": "代码可用",
      "type": "boolean",
      "required": false,
      "order": 8,
      
      "description": "是否提供源代码",
      
      "extraction": {
        "mode": "ai",
        "prompt": "Is the source code publicly available? Answer yes or no.",
        "confidence_threshold": 0.8
      },
      
      "display": {
        "width": 100,
        "align": "center",
        "format": "yes_no"
      }
    },
    
    {
      "id": "strengths",
      "name": "Strengths",
      "name_zh": "优势",
      "type": "long-text",
      "required": false,
      "order": 9,
      
      "description": "方法的主要优势",
      
      "validation": {
        "max_length": 1000
      },
      
      "extraction": {
        "mode": "ai",
        "prompt": "What are the main strengths or advantages of this method? Summarize in 2-3 sentences.",
        "confidence_threshold": 0.7
      },
      
      "display": {
        "width": 250,
        "align": "left",
        "format": "multiline"
      }
    },
    
    {
      "id": "limitations",
      "name": "Limitations",
      "name_zh": "局限性",
      "type": "long-text",
      "required": false,
      "order": 10,
      
      "description": "方法的局限性",
      
      "validation": {
        "max_length": 1000
      },
      
      "extraction": {
        "mode": "ai",
        "prompt": "What are the limitations or weaknesses of this method? Summarize in 2-3 sentences.",
        "confidence_threshold": 0.7
      },
      
      "display": {
        "width": 250,
        "align": "left",
        "format": "multiline"
      }
    },
    
    {
      "id": "notes",
      "name": "Notes",
      "name_zh": "备注",
      "type": "long-text",
      "required": false,
      "order": 11,
      
      "description": "其他备注信息",
      
      "extraction": {
        "mode": "manual",
        "prompt": null
      },
      
      "display": {
        "width": 200,
        "align": "left",
        "format": "multiline"
      }
    }
  ],
  
  "extraction_config": {
    "batch_size": 5,
    "retry_on_error": true,
    "max_retries": 3,
    "parallel_extraction": true,
    "save_raw_response": true
  }
}
```

---

### 2. ProjectSchema Model (关联表)

```python
class ProjectSchema(models.Model):
    """
    Project 与 Schema 的关联表
    表示某个 Project 应用了某个 Schema
    """
    
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, related_name="project_schemas", on_delete=models.CASCADE)
    schema = models.ForeignKey(Schema, related_name="project_schemas", on_delete=models.CASCADE)
    
    # 关联配置
    alias = models.CharField(
        max_length=255, 
        blank=True, null=True,
        help_text="在此 Project 中的别名（可选）"
    )
    
    # 覆盖字段（可选）
    field_overrides = models.TextField(
        blank=True, null=True,
        help_text="覆盖 Schema 中的某些字段配置（JSON）"
    )
    
    # 状态
    is_active = models.BooleanField(default=True)
    
    # 统计
    extraction_count = models.IntegerField(default=0, help_text="已提取的 Paper 数量")
    
    created_at = models.BigIntegerField(blank=True, null=True)
    
    class Meta:
        db_table = "project_schemas"
        unique_together = ("project", "schema")
        ordering = ["project", "created_at"]
    
    def __str__(self):
        return f"{self.project.project_id} → {self.schema.name}"
```

---

### 3. Extraction Model (增强版)

```python
class Extraction(models.Model):
    """
    单篇 Paper 在某个 Schema 下的提取结果
    Paper × Schema = Extraction (一个表格的一行)
    """
    
    id = models.AutoField(primary_key=True)
    
    # 关联
    paper = models.ForeignKey(Paper, related_name="extractions", on_delete=models.CASCADE)
    project = models.ForeignKey(Project, related_name="extractions", on_delete=models.CASCADE)
    schema = models.ForeignKey(Schema, related_name="extractions", on_delete=models.CASCADE)
    
    # 提取数据（核心）
    extracted_data = models.TextField(help_text="提取的结构化数据（JSON）")
    
    # 提取元数据
    extraction_method = models.CharField(
        max_length=20,
        choices=[
            ('ai', 'AI Extracted'),
            ('manual', 'Manual Entry'),
            ('hybrid', 'AI + Manual'),
            ('imported', 'Imported')
        ],
        default='ai'
    )
    
    # AI 相关
    model = models.CharField(max_length=255, blank=True, null=True)
    prompt_tokens = models.IntegerField(blank=True, null=True)
    completion_tokens = models.IntegerField(blank=True, null=True)
    
    # 状态
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('verified', 'Verified'),
        ],
        default='pending'
    )
    
    error_msg = models.TextField(blank=True, null=True)
    
    # 质量控制
    confidence_score = models.FloatField(blank=True, null=True, help_text="整体置信度 0-1")
    needs_review = models.BooleanField(default=False, help_text="是否需要人工审核")
    
    # 审计
    extracted_by = models.CharField(max_length=100, blank=True, null=True)
    verified_by = models.CharField(max_length=100, blank=True, null=True)
    verified_at = models.BigIntegerField(blank=True, null=True)
    
    created_at = models.BigIntegerField(blank=True, null=True)
    updated_at = models.BigIntegerField(blank=True, null=True)
    
    class Meta:
        db_table = "extractions"
        unique_together = ("paper", "project", "schema")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['project', 'schema', 'status']),
            models.Index(fields=['paper', 'schema']),
        ]
    
    def __str__(self):
        return f"{self.paper.paper_id} × {self.schema.name}"
```

#### extracted_data JSON 结构

```json
{
  "fields": {
    "method_name": {
      "value": "ResNet-50",
      "confidence": 0.95,
      "source": {
        "type": "ai",
        "location": "Section 3.2, Page 5",
        "raw_text": "We use ResNet-50 as our backbone network...",
        "timestamp": "2025-10-02T10:30:00Z"
      }
    },
    
    "dataset": {
      "value": "ImageNet",
      "confidence": 0.92,
      "source": {
        "type": "ai",
        "location": "Section 4.1, Table 1",
        "raw_text": "Experiments are conducted on ImageNet dataset",
        "timestamp": "2025-10-02T10:30:01Z"
      }
    },
    
    "accuracy": {
      "value": 92.1,
      "confidence": 0.88,
      "source": {
        "type": "ai",
        "location": "Table 2, Page 8",
        "raw_text": "Our method achieves 92.1% accuracy",
        "timestamp": "2025-10-02T10:30:02Z"
      }
    },
    
    "model_type": {
      "value": "cnn",
      "confidence": 0.98,
      "source": {
        "type": "ai",
        "location": "Introduction",
        "timestamp": "2025-10-02T10:30:03Z"
      }
    },
    
    "application_domains": {
      "value": ["cv"],
      "confidence": 0.94,
      "source": {
        "type": "ai",
        "location": "Abstract",
        "timestamp": "2025-10-02T10:30:04Z"
      }
    },
    
    "training_time": {
      "value": 24.5,
      "confidence": 0.75,
      "source": {
        "type": "ai",
        "location": "Section 4.2",
        "raw_text": "Training takes approximately 24.5 hours on 4 V100 GPUs",
        "timestamp": "2025-10-02T10:30:05Z"
      }
    },
    
    "hardware": {
      "value": "4x NVIDIA V100",
      "confidence": 0.92,
      "source": {
        "type": "ai",
        "location": "Section 4.2",
        "raw_text": "Training takes approximately 24.5 hours on 4 V100 GPUs",
        "timestamp": "2025-10-02T10:30:05Z"
      }
    },
    
    "code_available": {
      "value": true,
      "confidence": 0.99,
      "source": {
        "type": "ai",
        "location": "Abstract, Footnote",
        "raw_text": "Code is available at github.com/...",
        "timestamp": "2025-10-02T10:30:06Z"
      }
    },
    
    "strengths": {
      "value": "High accuracy with efficient training. Achieves state-of-the-art results on ImageNet benchmark. Architecture is modular and easy to extend.",
      "confidence": 0.82,
      "source": {
        "type": "ai",
        "location": "Conclusion, Section 5",
        "timestamp": "2025-10-02T10:30:07Z"
      }
    },
    
    "limitations": {
      "value": "High computational cost during inference. Requires large amounts of training data. Performance degrades on out-of-distribution samples.",
      "confidence": 0.79,
      "source": {
        "type": "ai",
        "location": "Discussion, Section 6",
        "timestamp": "2025-10-02T10:30:08Z"
      }
    },
    
    "notes": {
      "value": "重点关注 Table 2 的对比实验结果",
      "confidence": 1.0,
      "source": {
        "type": "manual",
        "user": "researcher_001",
        "timestamp": "2025-10-02T14:20:00Z"
      }
    }
  },
  
  "metadata": {
    "schema_id": "ml_methods_v1",
    "schema_version": "1.0",
    "extraction_time": "2025-10-02T10:30:00Z",
    "extraction_duration": 15.5,
    "model_used": "gpt-4o",
    "total_tokens": 3200,
    "average_confidence": 0.88,
    "fields_with_low_confidence": ["training_time", "limitations"],
    "extraction_warnings": [
      "Training time value has low confidence (0.75)",
      "Limitations field may need manual review"
    ]
  }
}
```

---

## 📋 字段类型定义

### 支持的字段类型

```python
FIELD_TYPES = {
    # 文本类
    'text': {
        'description': '短文本（单行）',
        'validation': ['max_length', 'pattern'],
        'extraction': ['ai', 'manual'],
        'display': 'input'
    },
    
    'long-text': {
        'description': '长文本（多行）',
        'validation': ['max_length'],
        'extraction': ['ai', 'manual'],
        'display': 'textarea'
    },
    
    # 数值类
    'number': {
        'description': '数值（整数或小数）',
        'validation': ['min', 'max', 'decimal_places'],
        'extraction': ['ai', 'manual'],
        'display': 'number_input',
        'supports_unit': True
    },
    
    'integer': {
        'description': '整数',
        'validation': ['min', 'max'],
        'extraction': ['ai', 'manual'],
        'display': 'number_input'
    },
    
    # 选择类
    'select': {
        'description': '单选（下拉框）',
        'requires': ['options'],
        'extraction': ['ai', 'manual'],
        'display': 'dropdown'
    },
    
    'multi-select': {
        'description': '多选（复选框）',
        'requires': ['options'],
        'extraction': ['ai', 'manual'],
        'display': 'checkbox_group'
    },
    
    'boolean': {
        'description': '是/否',
        'extraction': ['ai', 'manual'],
        'display': 'checkbox'
    },
    
    # 日期时间
    'date': {
        'description': '日期',
        'validation': ['min_date', 'max_date'],
        'extraction': ['ai', 'manual'],
        'display': 'date_picker'
    },
    
    'year': {
        'description': '年份',
        'validation': ['min', 'max'],
        'extraction': ['ai', 'manual'],
        'display': 'year_input'
    },
    
    # 列表类
    'multi-text': {
        'description': '文本列表',
        'validation': ['max_items', 'max_length_per_item'],
        'extraction': ['ai', 'manual'],
        'display': 'tag_input'
    },
    
    # 评分类
    'rating': {
        'description': '评分（1-5星）',
        'validation': ['min', 'max'],
        'extraction': ['manual'],
        'display': 'star_rating'
    },
    
    # URL 类
    'url': {
        'description': 'URL 链接',
        'validation': ['pattern'],
        'extraction': ['ai', 'manual'],
        'display': 'url_input'
    }
}
```

---

## 🎨 UI/UX 设计

### 1. Schema Library 页面

```
┌──────────────────────────────────────────────────────────┐
│ Schema Library                    [+ Create Schema]      │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ [Search schemas...]    [Category: All ▼]  [Sort: Usage ▼]│
│                                                          │
│ Official Templates (5)                                   │
│ ┌────────────────────────────────────────────────────┐  │
│ │ 📊 ML Methods Comparison Template                  │  │
│ │    10 fields • Used in 15 projects                 │  │
│ │    🔒 Locked (In Use)                              │  │
│ │    [Preview] [Use in Project] [Duplicate]          │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ 🔒 Security Mechanisms                             │  │
│ │    8 fields • Used in 8 projects                   │  │
│ │    🔒 Locked (In Use)                              │  │
│ │    [Preview] [Use in Project] [Duplicate]          │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ My Schemas (3)                                           │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ 📈 Performance Evaluation v2                       │  │
│ │    12 fields • Used in 2 projects • 45 extractions │  │
│ │    🔒 Locked (In Use)                              │  │
│ │    [Preview] [Use in Project] [Duplicate]          │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ 🎯 My IoT Analysis                                 │  │
│ │    8 fields • Not used yet                         │  │
│ │    📝 Draft (Can Edit)                             │  │
│ │    [Preview] [Use in Project] [Edit] [Delete]      │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ 📊 ML Methods v3 (Draft)                           │  │
│ │    11 fields • Not used yet                        │  │
│ │    📝 Draft (Can Edit)                             │  │
│ │    ↳ Derived from: ML Methods v2                   │  │
│ │    [Preview] [Continue Editing] [Delete]           │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 2. Schema Editor 页面

```
┌──────────────────────────────────────────────────────────┐
│ Create Schema                                       [×]  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Basic Information                                        │
│ ┌──────────────────────────────────────────────────┐    │
│ │ Schema ID: [ml_methods_comparison            ]   │    │
│ │ Name: [ML Methods Comparison                 ]   │    │
│ │ Category: [Machine Learning ▼]                   │    │
│ │ Description:                                      │    │
│ │ ┌──────────────────────────────────────────────┐│    │
│ │ │ Compare different ML methods and models     ││    │
│ │ └──────────────────────────────────────────────┘│    │
│ └──────────────────────────────────────────────────┘    │
│                                                          │
│ Fields                                  [+ Add Field]    │
│                                                          │
│ ┌──────────────────────────────────────────────────────┐│
│ │ 1. Method Name                      [↑] [↓] [×]     ││
│ │    Type: [Text ▼]     Required: ☑                   ││
│ │    Extraction: [AI ▼] Manual: ☑                     ││
│ │                                                      ││
│ │    AI Prompt:                                        ││
│ │    ┌────────────────────────────────────────────┐  ││
│ │    │ What is the name of the ML method?        │  ││
│ │    └────────────────────────────────────────────┘  ││
│ │                                                      ││
│ │    [▼ Advanced Options]                              ││
│ └──────────────────────────────────────────────────────┘│
│                                                          │
│ ┌──────────────────────────────────────────────────────┐│
│ │ 2. Accuracy (%)                     [↑] [↓] [×]     ││
│ │    Type: [Number ▼]   Required: ☐                   ││
│ │    Range: [0] - [100]  Unit: [%]                    ││
│ │    Extraction: [AI ▼] Manual: ☑                     ││
│ │                                                      ││
│ │    AI Prompt:                                        ││
│ │    ┌────────────────────────────────────────────┐  ││
│ │    │ What is the accuracy? Provide number.     │  ││
│ │    └────────────────────────────────────────────┘  ││
│ └──────────────────────────────────────────────────────┘│
│                                                          │
│ Quick Add from Template:                                 │
│ [Common Fields ▼]  → Method, Dataset, Accuracy, Year... │
│                                                          │
│ Preview Table:                                           │
│ ┌──────┬────────────┬──────────┬──────────┐            │
│ │Paper │Method Name │Accuracy  │Dataset   │            │
│ ├──────┼────────────┼──────────┼──────────┤            │
│ │A01   │CNN         │98.5%     │MNIST     │            │
│ │A02   │LSTM        │95.2%     │IMDB      │            │
│ └──────┴────────────┴──────────┴──────────┘            │
│                                                          │
│                      [Cancel]  [Save Schema]             │
└──────────────────────────────────────────────────────────┘
```

### 3. Project - Apply Schema 页面

```
Project: Literature Survey on IoT Security

┌──────────────────────────────────────────────────────────┐
│ Schemas                               [+ Apply Schema]   │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Applied Schemas (2)                                      │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ 🔒 Security Mechanisms                             │  │
│ │    8 fields • 15/15 papers extracted               │  │
│ │    Status: ✓ Complete                              │  │
│ │                                                    │  │
│ │    [View Table] [Export Excel] [Remove Schema]     │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ 📈 Performance Evaluation                          │  │
│ │    12 fields • 10/15 papers extracted              │  │
│ │    Status: ⏳ In Progress (5 pending)              │  │
│ │                                                    │  │
│ │    [View Table] [Run AI Extraction] [Remove]       │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 4. Extraction Table View (核心界面)

```
Project: IoT Security > Schema: Security Mechanisms

┌──────────────────────────────────────────────────────────────┐
│ Security Mechanisms                                          │
│ [Export ▼] [Run AI Extraction] [Import] [Settings]          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Progress: 15/15 extracted  ✓ 12 verified  ⚠ 3 need review  │
│                                                              │
│ [Search...] [Filter: All ▼] [Confidence: All ▼] [Sort ▼]   │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐│
│ │📄│Paper  │Algorithm│Auth    │Perf%│Use Cases│Status   ││ │
│ ├──┼───────┼─────────┼────────┼─────┼─────────┼─────────┼┤│
│ │✓│[A01]  │AES-256  │PKI     │15.0 │IoT,Cloud│✓ Done  ││☰││
│ │✓│[A02]  │RSA-2048 │OAuth   │8.0  │Edge     │✓ Done  ││☰││
│ │⚠│[A03]  │ChaCha20 │JWT     │12.0 │IoT,BC   │⚠ Review││☰││
│ │⏳│[A04]  │─        │─       │─    │─        │⏳ Pending││☰││
│ │✓│[A05]  │ECC-256  │BC Auth │5.0  │Mobile   │✓ Done  ││☰││
│ └──────────────────────────────────────────────────────────┘│
│                                                              │
│ Quick Actions:                                               │
│ • Run AI Extraction for 1 pending paper                     │
│ • Review 3 items with low confidence                        │
│ • Export complete table to Excel                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘

点击某行展开 → 详细编辑界面
```

### 5. Extraction Detail Edit 页面

```
Paper: [A03] Secure Consensus Mechanisms
Schema: Security Mechanisms Comparison

┌──────────────────────────────────────────────────────────┐
│ Extraction Editor                    [Save] [AI Re-run]  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Overall: ⚠ Needs Review  Confidence: 85%  AI: gpt-4o    │
│                                                          │
│ ┌─ Encryption Algorithm ─────────────────────────────┐  │
│ │ * Required                                         │  │
│ │ [ChaCha20-Poly1305                              ] │  │
│ │                                                    │  │
│ │ AI Confidence: 95% ✅                              │  │
│ │ Source: Section 3.2, Page 5                       │  │
│ │ "We employ ChaCha20-Poly1305 for encryption..."   │  │
│ │ [Show full context ▼]                             │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ ┌─ Authentication Method ────────────────────────────┐  │
│ │ * Required                                         │  │
│ │ ○ PKI  ● JWT  ○ OAuth  ○ Blockchain  ○ Other     │  │
│ │                                                    │  │
│ │ AI Confidence: 88% ✅                              │  │
│ │ Source: Section 4.1, Page 7                       │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ ┌─ Performance Overhead (%) ─────────────────────────┐  │
│ │ [12.0        ] %                                   │  │
│ │                                                    │  │
│ │ AI Confidence: 75% ⚠ LOW                          │  │
│ │ Source: Table 2, Page 8 (inferred)                │  │
│ │ ⚠ Please verify this value                        │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ ┌─ Use Cases ────────────────────────────────────────┐  │
│ │ ☑ IoT    ☐ Cloud    ☐ Edge    ☑ Blockchain        │  │
│ │ ☐ Mobile                                           │  │
│ │                                                    │  │
│ │ AI Confidence: 91% ✅                              │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ [View PDF] [Chat with AI] [Mark as Verified]             │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## � Schema 复制功能（Duplicate）

### 复制对话框

```
┌─────────────────────────────────────────────────────┐
│ Duplicate Schema                               [×]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│ You are duplicating:                                │
│ 📊 ML Methods Comparison v2                        │
│    (10 fields, used in 2 projects)                 │
│                                                     │
│ New Schema Information:                             │
│ ┌─────────────────────────────────────────────┐    │
│ │ Schema ID: [ml_methods_v3                ]  │    │
│ │ Name: [ML Methods Comparison v3          ]  │    │
│ │ Category: [Machine Learning ▼]              │    │
│ │ Description:                                 │    │
│ │ ┌─────────────────────────────────────────┐│    │
│ │ │ Updated version with training time field││    │
│ │ └─────────────────────────────────────────┘│    │
│ └─────────────────────────────────────────────┘    │
│                                                     │
│ ✓ Copy all 10 fields from original                 │
│ ✓ Copy AI prompts and validation rules             │
│ ✓ Link to parent schema (for tracking)             │
│                                                     │
│ After creation, you can:                            │
│ • Modify fields (add/remove/edit)                   │
│ • Update AI prompts                                 │
│ • Save as new schema                                │
│                                                     │
│ Note: Original schema will remain unchanged         │
│                                                     │
│                    [Cancel]  [Duplicate & Edit]     │
└─────────────────────────────────────────────────────┘
```

### Schema 详情页面（锁定状态）

```
┌─────────────────────────────────────────────────────────┐
│ Schema: ML Methods Comparison v2              [◄ Back] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Status: 🔒 Locked (In Use)                              │
│ Used in: 2 projects • 45 extractions completed         │
│                                                         │
│ ⚠️ This schema is locked and cannot be modified        │
│ It is currently being used by projects and extractions.│
│ To make changes, duplicate this schema to create a new │
│ version.                                                │
│                                                         │
│ [Duplicate Schema]  [View Usage]  [Export Definition]  │
│                                                         │
│ Fields (10):                                            │
│ ┌───────────────────────────────────────────────────┐  │
│ │ 1. Method Name (text) *                           │  │
│ │    AI Prompt: "What is the name of the ML..."     │  │
│ │    Required: Yes                                  │  │
│ │                                                   │  │
│ │ 2. Dataset (text) *                               │  │
│ │    AI Prompt: "What dataset is used..."           │  │
│ │    Required: Yes                                  │  │
│ │                                                   │  │
│ │ 3. Accuracy (number)                              │  │
│ │    Range: 0-100, Unit: %                          │  │
│ │    AI Prompt: "What is the accuracy..."           │  │
│ │                                                   │  │
│ │ [Show all 10 fields ▼]                            │  │
│ └───────────────────────────────────────────────────┘  │
│                                                         │
│ Usage History:                                          │
│ • Project "IoT Security Survey" - 20 extractions       │
│ • Project "ML Benchmarks" - 25 extractions             │
│                                                         │
│ Derived Schemas:                                        │
│ • ML Methods v3 (Draft) - Created 2025-10-01           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Schema 详情页面（草稿状态）

```
┌─────────────────────────────────────────────────────────┐
│ Schema: My IoT Analysis (Draft)               [◄ Back] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Status: 📝 Draft (Not Used Yet)                         │
│ You can freely edit this schema until it's first used. │
│                                                         │
│ [Edit Schema]  [Delete Schema]  [Export Definition]    │
│                                                         │
│ Fields (8):                                             │
│ ┌───────────────────────────────────────────────────┐  │
│ │ 1. Device Type (select) *                         │  │
│ │    Options: Sensor, Gateway, Actuator, Cloud     │  │
│ │    AI Prompt: "What type of IoT device..."        │  │
│ │                                                   │  │
│ │ 2. Communication Protocol (multi-select)          │  │
│ │    Options: WiFi, BLE, LoRa, Zigbee, 5G          │  │
│ │    AI Prompt: "What communication protocols..."   │  │
│ │                                                   │  │
│ │ [Show all 8 fields ▼]                             │  │
│ └───────────────────────────────────────────────────┘  │
│                                                         │
│ ⚠️ Warning: Once this schema is used in a project or   │
│ for extraction, it will be locked and cannot be edited.│
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## �🚀 实现路线图

### Phase 1: 数据库与核心模型（Week 1）
- [ ] 创建 Schema 模型
- [ ] 创建 ProjectSchema 关联模型
- [ ] 增强 Extraction 模型（添加 schema 外键）
- [ ] 数据库迁移脚本
- [ ] 基础 API endpoints

### Phase 2: Schema Library（Week 2）
- [ ] Schema CRUD 功能
- [ ] Schema Library 列表页
- [ ] Schema 详情/预览页
- [ ] Schema 模板库（预设）
- [ ] Schema 导入/导出

### Phase 3: Schema Editor（Week 3）
- [ ] 字段类型组件
- [ ] 拖拽排序功能
- [ ] AI Prompt 编辑
- [ ] 验证规则配置
- [ ] 预览表格生成

### Phase 4: Project Integration（Week 4）
- [ ] Project 应用 Schema 功能
- [ ] Schema 列表展示
- [ ] 批量 AI 提取触发
- [ ] 进度追踪

### Phase 5: Extraction Table View（Week 5-6）
- [ ] Excel-like 表格组件
- [ ] 行内编辑功能
- [ ] 筛选和排序
- [ ] 状态管理
- [ ] 批量操作

### Phase 6: Extraction Editor（Week 7）
- [ ] 详细编辑界面
- [ ] 置信度显示
- [ ] 来源定位
- [ ] AI 重提取
- [ ] PDF 联动

### Phase 7: Export & Analysis（Week 8）
- [ ] Excel 导出（格式化）
- [ ] CSV 导出
- [ ] LaTeX 表格生成
- [ ] 统计分析
- [ ] 数据可视化

---

## 💡 关键技术点

### 1. AI 提取策略

```python
class ExtractionStrategy:
    """AI 提取策略"""
    
    STRATEGIES = {
        'semantic_search': {
            'description': '语义搜索相关段落后提取',
            'steps': [
                '1. 识别字段相关的段落',
                '2. 提取候选答案',
                '3. 验证和规范化'
            ]
        },
        
        'full_text': {
            'description': '基于全文的提取',
            'steps': [
                '1. 读取整篇论文',
                '2. 一次性提取所有字段',
                '3. 返回结构化结果'
            ]
        },
        
        'qa': {
            'description': '问答式提取',
            'steps': [
                '1. 对每个字段构造问题',
                '2. 基于论文回答问题',
                '3. 提取答案'
            ]
        },
        
        'table_extraction': {
            'description': '从表格中提取',
            'steps': [
                '1. 定位相关表格',
                '2. 解析表格结构',
                '3. 提取数值'
            ]
        }
    }
```

### 2. 字段验证

```python
def validate_field(field_definition, value):
    """验证字段值"""
    
    field_type = field_definition['type']
    validation = field_definition.get('validation', {})
    
    validators = {
        'text': lambda v: len(v) <= validation.get('max_length', 1000),
        'number': lambda v: validation.get('min', -float('inf')) <= v <= validation.get('max', float('inf')),
        'select': lambda v: v in [opt['value'] for opt in field_definition['options']],
        'multi-select': lambda v: all(item in [opt['value'] for opt in field_definition['options']] for item in v),
        'boolean': lambda v: isinstance(v, bool),
        'date': lambda v: validate_date(v, validation),
        'url': lambda v: validate_url(v),
    }
    
    return validators.get(field_type, lambda v: True)(value)
```

### 3. 导出格式

```python
class SchemaExporter:
    """Schema 数据导出器"""
    
    def export_to_excel(self, project, schema):
        """导出为 Excel"""
        wb = openpyxl.Workbook()
        
        # Sheet 1: Metadata
        meta_sheet = wb.active
        meta_sheet.title = "Metadata"
        # ... 写入元数据
        
        # Sheet 2: Data
        data_sheet = wb.create_sheet("Data")
        # ... 写入提取数据
        
        # Sheet 3: AI Metadata
        ai_sheet = wb.create_sheet("AI Metadata")
        # ... 写入置信度等信息
        
        return wb
    
    def export_to_latex(self, project, schema):
        """导出为 LaTeX 表格"""
        template = r"""
\begin{table}[h]
\centering
\caption{%s}
\label{tab:%s}
\begin{tabular}{%s}
\hline
%s \\
\hline
%s
\hline
\end{tabular}
\end{table}
        """
        # ... 生成 LaTeX 代码
        return template % (...)
```

---

## ✅ 总结

这个设计的核心优势：

1. **Schema Library 模式** - 全局共享，可复用
2. **灵活的字段系统** - 支持多种类型和验证
3. **AI + Manual 双模式** - 既能自动化又能手动控制
4. **完整的工作流** - 从创建到导出的闭环
5. **质量保证** - 置信度、来源、审核机制
6. **面向输出** - 直接生成论文所需的表格

下一步你想：
1. 开始实现数据库模型？
2. 创建 Schema Editor UI？
3. 讨论更多细节？

