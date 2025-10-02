# Feature Group Enhancement Design

## 🎯 目标

将 Feature Group 从简单的字段集合升级为**结构化数据表生成器**，支持：
1. 定义复杂的字段类型和验证规则
2. 从每篇 paper 提取数据填充到表格
3. 生成可导出的结构化数据表（Excel/CSV）
4. 支持数据可视化和统计分析
5. 用于撰写文章时的数据引用和综合

---

## 📊 核心概念

### Feature Group = 数据表模板

```
Feature Group: "Security Mechanisms Comparison"
├─ Fields (列定义):
│  ├─ Paper ID (自动)
│  ├─ Citation Key (自动)
│  ├─ Encryption Algorithm (文本)
│  ├─ Authentication Method (单选)
│  ├─ Performance Overhead (数值)
│  ├─ Use Cases (多选)
│  └─ Pros & Cons (长文本)
│
└─ Extractions (行数据):
   ├─ Paper A → [AES-256, PKI, 15%, [IoT, Cloud], "..."]
   ├─ Paper B → [RSA-2048, OAuth, 8%, [Edge], "..."]
   └─ Paper C → [ChaCha20, JWT, 12%, [IoT, Blockchain], "..."]

最终导出:
┌─────────┬──────────┬────────────┬───────┬──────────┐
│ Paper   │ Algorithm│ Auth Method│ Perf% │ Use Cases│
├─────────┼──────────┼────────────┼───────┼──────────┤
│ Paper A │ AES-256  │ PKI        │ 15%   │ IoT,Cloud│
│ Paper B │ RSA-2048 │ OAuth      │ 8%    │ Edge     │
│ Paper C │ ChaCha20 │ JWT        │ 12%   │ IoT,BC   │
└─────────┴──────────┴────────────┴───────┴──────────┘
```

---

## 🗄️ 数据库设计

### 1. ProjectGroup 增强

```python
class ProjectGroup(models.Model):
    """Feature Group - 定义数据表结构"""
    
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, related_name="feature_groups", on_delete=models.CASCADE)
    group_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # 字段定义（JSON）
    fields_schema = models.TextField(help_text="字段定义的 JSON schema")
    
    # AI 提取配置
    extraction_prompt_template = models.TextField(
        blank=True, null=True,
        help_text="AI 提取的 prompt 模板，可以包含 {field_name}, {field_description} 等占位符"
    )
    
    # 元数据
    created_at = models.BigIntegerField(blank=True, null=True)
    updated_at = models.BigIntegerField(blank=True, null=True)
    
    class Meta:
        db_table = "project_groups"
        unique_together = ("project", "group_name")
        ordering = ["project", "group_name"]
```

#### fields_schema 结构

```json
{
  "version": "1.0",
  "fields": [
    {
      "id": "encryption_algorithm",
      "name": "加密算法",
      "type": "text",
      "description": "论文中使用的加密算法名称",
      "required": true,
      "validation": {
        "max_length": 100
      },
      "extraction_prompt": "What encryption algorithm is mentioned in this paper? Provide the specific name.",
      "display_order": 1
    },
    {
      "id": "authentication_method",
      "name": "认证方式",
      "type": "select",
      "description": "身份认证方法",
      "required": true,
      "options": [
        {"value": "pki", "label": "PKI"},
        {"value": "oauth", "label": "OAuth"},
        {"value": "jwt", "label": "JWT"},
        {"value": "blockchain", "label": "Blockchain-based"},
        {"value": "other", "label": "Other"}
      ],
      "extraction_prompt": "What authentication method is used? Choose from: PKI, OAuth, JWT, Blockchain-based, or Other.",
      "display_order": 2
    },
    {
      "id": "performance_overhead",
      "name": "性能开销",
      "type": "number",
      "description": "相比基准方案的性能开销（百分比）",
      "required": false,
      "validation": {
        "min": 0,
        "max": 100
      },
      "unit": "%",
      "extraction_prompt": "What is the performance overhead compared to baseline? Provide a percentage if mentioned.",
      "display_order": 3
    },
    {
      "id": "use_cases",
      "name": "应用场景",
      "type": "multi-select",
      "description": "论文涉及的应用场景",
      "required": false,
      "options": [
        {"value": "iot", "label": "IoT"},
        {"value": "cloud", "label": "Cloud Computing"},
        {"value": "edge", "label": "Edge Computing"},
        {"value": "blockchain", "label": "Blockchain"},
        {"value": "mobile", "label": "Mobile"}
      ],
      "extraction_prompt": "What are the application scenarios mentioned? Select all that apply from: IoT, Cloud, Edge, Blockchain, Mobile.",
      "display_order": 4
    },
    {
      "id": "evaluation_metrics",
      "name": "评估指标",
      "type": "multi-text",
      "description": "论文中使用的评估指标",
      "required": false,
      "extraction_prompt": "List all evaluation metrics used in this paper (e.g., throughput, latency, energy consumption).",
      "display_order": 5
    },
    {
      "id": "dataset",
      "name": "数据集",
      "type": "text",
      "description": "实验使用的数据集",
      "required": false,
      "extraction_prompt": "What dataset is used for evaluation?",
      "display_order": 6
    },
    {
      "id": "year_published",
      "name": "发表年份",
      "type": "number",
      "description": "论文发表年份",
      "required": false,
      "validation": {
        "min": 2000,
        "max": 2030
      },
      "extraction_prompt": "What year was this paper published?",
      "display_order": 7
    },
    {
      "id": "strengths",
      "name": "优势",
      "type": "long-text",
      "description": "论文方法的主要优势",
      "required": false,
      "extraction_prompt": "What are the main strengths or advantages of the proposed method?",
      "display_order": 8
    },
    {
      "id": "limitations",
      "name": "局限性",
      "type": "long-text",
      "description": "论文方法的局限性",
      "required": false,
      "extraction_prompt": "What are the limitations of the proposed method?",
      "display_order": 9
    },
    {
      "id": "is_relevant",
      "name": "相关性",
      "type": "boolean",
      "description": "该论文是否与研究问题高度相关",
      "required": true,
      "extraction_prompt": "Is this paper highly relevant to the research question?",
      "display_order": 10
    }
  ]
}
```

### 2. Extraction 增强

```python
class Extraction(models.Model):
    """单篇论文在某个 Feature Group 中的提取结果"""
    
    id = models.AutoField(primary_key=True)
    
    # 关联
    paper = models.ForeignKey(Paper, related_name="extractions", on_delete=models.CASCADE)
    project = models.ForeignKey(Project, related_name="extractions", on_delete=models.CASCADE, blank=True, null=True)
    group = models.ForeignKey(
        'projects.ProjectGroup',
        related_name="extractions",
        on_delete=models.CASCADE,
        null=True,  # 兼容旧数据
        help_text="所属的 Feature Group"
    )
    
    # 提取结果（JSON）
    extracted_data = models.TextField(help_text="提取的结构化数据")
    
    # AI 元数据
    model = models.CharField(max_length=255)
    prompt_tokens = models.IntegerField(blank=True, null=True)
    completion_tokens = models.IntegerField(blank=True, null=True)
    
    # 状态
    status = models.CharField(
        max_length=64,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('verified', 'Verified'),  # 人工验证通过
        ]
    )
    error_msg = models.TextField(blank=True, null=True)
    
    # 审计
    extracted_by = models.CharField(max_length=100, blank=True, null=True, help_text="AI 或用户")
    verified_by = models.CharField(max_length=100, blank=True, null=True, help_text="验证人")
    created_at = models.BigIntegerField(blank=True, null=True)
    updated_at = models.BigIntegerField(blank=True, null=True)
    
    class Meta:
        db_table = "extractions"
        ordering = ["-created_at"]
        unique_together = ("paper", "group")  # 每篇 paper 在每个 group 中只有一条记录
```

#### extracted_data 结构

```json
{
  "fields": {
    "encryption_algorithm": {
      "value": "AES-256-GCM",
      "confidence": 0.95,
      "source": "Section 3.2, Page 5, Paragraph 2",
      "raw_text": "We employ AES-256-GCM for data encryption..."
    },
    "authentication_method": {
      "value": "pki",
      "confidence": 0.88,
      "source": "Section 4.1, Page 7"
    },
    "performance_overhead": {
      "value": 15.5,
      "confidence": 0.82,
      "source": "Table 2, Page 8",
      "raw_text": "The overhead is approximately 15.5% compared to baseline."
    },
    "use_cases": {
      "value": ["iot", "edge"],
      "confidence": 0.91,
      "source": "Abstract, Introduction"
    },
    "is_relevant": {
      "value": true,
      "confidence": 0.98
    }
  },
  "metadata": {
    "extraction_time": "2025-10-02T16:30:00Z",
    "model_used": "gpt-4o",
    "total_tokens": 2500,
    "extraction_method": "ai",  # ai, manual, hybrid
    "notes": "High confidence extraction"
  }
}
```

---

## 🎨 UI/UX 设计

### 1. Feature Group 创建/编辑界面

```
┌─────────────────────────────────────────────────────────┐
│ Create Feature Group                               [×]  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Group Name: [Security Mechanisms Comparison        ]   │
│                                                         │
│ Description:                                            │
│ ┌─────────────────────────────────────────────────┐   │
│ │ Compare security mechanisms used in IoT papers  │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ Fields:                                    [+ Add Field]│
│                                                         │
│ ┌─────────────────────────────────────────────────────┐│
│ │ 1. Encryption Algorithm               [↑] [↓] [×]   ││
│ │    Type: Text         Required: ☑                   ││
│ │    Description: The encryption algorithm used       ││
│ │    AI Prompt: What encryption algorithm...          ││
│ │    [Show Advanced Options ▼]                        ││
│ └─────────────────────────────────────────────────────┘│
│                                                         │
│ ┌─────────────────────────────────────────────────────┐│
│ │ 2. Authentication Method              [↑] [↓] [×]   ││
│ │    Type: Select       Required: ☑                   ││
│ │    Options: PKI, OAuth, JWT, Blockchain, Other      ││
│ │    [Show Advanced Options ▼]                        ││
│ └─────────────────────────────────────────────────────┘│
│                                                         │
│ ┌─────────────────────────────────────────────────────┐│
│ │ 3. Performance Overhead (%)           [↑] [↓] [×]   ││
│ │    Type: Number       Required: ☐                   ││
│ │    Range: 0 - 100     Unit: %                       ││
│ │    [Show Advanced Options ▼]                        ││
│ └─────────────────────────────────────────────────────┘│
│                                                         │
│ Templates:                                              │
│ [Load from Template ▼]                                  │
│  - Security Analysis                                    │
│  - Performance Evaluation                               │
│  - IoT Solutions Comparison                             │
│  - Custom...                                            │
│                                                         │
│                        [Cancel]  [Save Feature Group]   │
└─────────────────────────────────────────────────────────┘
```

### 2. Extraction 数据表视图

```
Project: Literature Survey > Groups > Security Mechanisms

┌─────────────────────────────────────────────────────────────────────┐
│ Security Mechanisms Comparison                    [Export ▼] [AI ⚡]│
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Papers: 15    Extracted: 12    Pending: 3                          │
│                                                                     │
│ [Search papers...]              [Filter: All ▼] [Sort: Paper ID ▼] │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐│
│ │Paper  │Algorithm │Auth Method│Perf%│Use Cases   │Status   │   ││
│ ├───────┼──────────┼───────────┼─────┼────────────┼─────────┼───┤│
│ │[A01]  │AES-256   │PKI        │15   │IoT, Cloud  │✓ Done   │ … ││
│ │[A02]  │RSA-2048  │OAuth      │8    │Edge        │✓ Done   │ … ││
│ │[A03]  │ChaCha20  │JWT        │12   │IoT, BC     │⚠ Review │ … ││
│ │[A04]  │─         │─          │─    │─           │⏳ Pending│ … ││
│ │[A05]  │ECC-256   │Blockchain │5    │Mobile      │✓ Done   │ … ││
│ └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│ Actions:                                                            │
│ [Run AI Extraction for Pending Papers]                             │
│ [Export to Excel]  [Export to CSV]  [Generate Summary]             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3. 单篇 Paper 的 Extraction 编辑界面

```
Paper: [A03] Secure Consensus Mechanisms for Blockchained IoT
Group: Security Mechanisms Comparison

┌─────────────────────────────────────────────────────────────┐
│ Extraction Editor                                 [AI Re-extract]│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Status: ⚠ Needs Review    Model: gpt-4o    Confidence: 85% │
│                                                             │
│ Encryption Algorithm *                                      │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ ChaCha20-Poly1305                                   │   │
│ └─────────────────────────────────────────────────────┘   │
│ Confidence: 95%  Source: Section 3.2, Page 5               │
│ [Show extracted text ▼]                                    │
│                                                             │
│ Authentication Method *                                     │
│ ○ PKI  ● JWT  ○ OAuth  ○ Blockchain  ○ Other              │
│ Confidence: 88%  Source: Section 4.1                       │
│                                                             │
│ Performance Overhead (%)                                    │
│ ┌─────┐ %                                                  │
│ │ 12  │                                                    │
│ └─────┘                                                    │
│ Confidence: 75%  Source: Table 2 (Inferred)                │
│ ⚠ Low confidence - please verify                           │
│                                                             │
│ Use Cases (Select all that apply)                          │
│ ☑ IoT    ☐ Cloud    ☐ Edge    ☑ Blockchain    ☐ Mobile   │
│ Confidence: 91%                                             │
│                                                             │
│ Strengths                                                   │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ - Low computational overhead                        │   │
│ │ - Suitable for resource-constrained devices        │   │
│ │ - Integration with blockchain for tamper-proof     │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                             │
│ Notes                                                       │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ Check performance numbers in original paper         │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                             │
│ [View PDF]  [Chat with AI]         [Cancel]  [Save & Verify]│
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 实现路线图

### Phase 1: 数据库增强（1周）
- [x] 设计新的 schema
- [ ] 创建数据库迁移
- [ ] 添加 `group` 字段到 Extraction
- [ ] 修改 ProjectGroup 的 fields 存储格式
- [ ] 数据迁移脚本（兼容旧数据）

### Phase 2: Field Schema Editor（2周）
- [ ] Feature Group 创建界面
- [ ] 字段类型支持（text, number, select, multi-select, boolean, long-text）
- [ ] 字段拖拽排序
- [ ] 模板库功能
- [ ] 导入/导出 schema

### Phase 3: Extraction Table View（2周）
- [ ] 数据表格视图（类似 Excel）
- [ ] 批量 AI 提取功能
- [ ] 状态管理（pending, completed, verified）
- [ ] 筛选和排序
- [ ] 行内编辑

### Phase 4: Extraction Editor（1周）
- [ ] 单篇 paper 的详细编辑界面
- [ ] 显示 AI 置信度
- [ ] 显示提取来源
- [ ] 人工修改和验证
- [ ] 与 PDF 联动

### Phase 5: Export & Analysis（1周）
- [ ] 导出为 Excel（带格式）
- [ ] 导出为 CSV
- [ ] 生成统计报告
- [ ] 数据可视化（图表）
- [ ] 生成综述表格（用于论文写作）

---

## 📤 导出格式示例

### Excel 导出结构

```
Sheet 1: Metadata
┌────────────────┬──────────────────────────────────┐
│ Project Name   │ Literature Survey                │
│ Feature Group  │ Security Mechanisms Comparison   │
│ Papers Total   │ 15                               │
│ Extracted      │ 12                               │
│ Export Date    │ 2025-10-02                       │
└────────────────┴──────────────────────────────────┘

Sheet 2: Extracted Data
┌────────┬────────────┬───────────┬──────────┬─────────────┬───────────┬──────────────┐
│Paper ID│Citation Key│Algorithm  │Auth Method│Performance %│Use Cases  │Strengths     │
├────────┼────────────┼───────────┼──────────┼─────────────┼───────────┼──────────────┤
│A01     │Zhang2023   │AES-256    │PKI       │15.0         │IoT, Cloud │High security │
│A02     │Li2024      │RSA-2048   │OAuth     │8.0          │Edge       │Fast auth     │
│A03     │Wang2023    │ChaCha20   │JWT       │12.0         │IoT, BC    │Low overhead  │
└────────┴────────────┴───────────┴──────────┴─────────────┴───────────┴──────────────┘

Sheet 3: AI Metadata
┌────────┬───────────┬────────────┬──────────────┬────────────┐
│Paper ID│Model Used │Confidence %│Extracted Date│Verified By │
├────────┼───────────┼────────────┼──────────────┼────────────┤
│A01     │gpt-4o     │92          │2025-10-01    │User        │
│A02     │gpt-4o     │88          │2025-10-01    │User        │
│A03     │gpt-4o     │85          │2025-10-02    │-           │
└────────┴───────────┴────────────┴──────────────┴────────────┘
```

---

## 🎯 与竞品对比

| Feature | EPPI-Reviewer | Scholarcy | Elicit | **SMS Extractor (Enhanced)** |
|---------|---------------|-----------|--------|------------------------------|
| Custom Fields | ✅ | ❌ | ❌ | ✅ Enhanced |
| Field Types | Basic | N/A | N/A | **10+ types** |
| AI Extraction | ✅ | ✅ | ✅ | ✅ + Confidence |
| Table View | ✅ | ❌ | ❌ | ✅ Excel-like |
| Batch Edit | ✅ | ❌ | ❌ | ✅ Planned |
| Export Format | Excel | Excel | CSV | **Excel + CSV + JSON** |
| Templates | ✅ | ❌ | ❌ | ✅ Planned |
| Open Source | ❌ | ❌ | ❌ | ✅ |

---

## 💡 使用场景示例

### 场景 1: IoT 安全综述

```
Feature Group: "IoT Security Solutions"

Fields:
- Solution Type (select): Encryption, Authentication, Access Control, Intrusion Detection
- Algorithm/Protocol (text)
- Device Type (multi-select): Sensor, Gateway, Cloud
- Scalability (select): Low, Medium, High
- Energy Efficiency (number): mW
- Latency (number): ms
- Security Level (select): Low, Medium, High
- Deployment Complexity (select): Easy, Moderate, Difficult
- Evaluation Dataset (text)
- Key Findings (long-text)

用于撰写:
- Section 3.1: Comparison of Security Solutions (Table 1)
- Section 4.2: Performance Analysis (Table 2)
```

### 场景 2: 机器学习方法对比

```
Feature Group: "ML Models Comparison"

Fields:
- Model Type (select): CNN, RNN, Transformer, GAN
- Dataset (text)
- Accuracy (%) (number)
- Training Time (hours) (number)
- Model Size (MB) (number)
- Hardware Requirements (multi-select): CPU, GPU, TPU
- Preprocessing Steps (multi-text)
- Hyperparameters (long-text)
- Limitations (long-text)

用于撰写:
- Table 3: Model Performance Comparison
- Figure 2: Accuracy vs Training Time
```

---

## 🔧 技术栈建议

### Backend
- Django Models 增强
- JSON Schema 验证（jsonschema library）
- Pandas for data export
- OpenPyXL for Excel generation

### Frontend
- AG Grid / Handsontable (表格编辑)
- React Hook Form (表单管理)
- Drag-and-drop (字段排序)
- Chart.js (数据可视化)

---

## ✅ 下一步

请选择你想先实现的部分：

1. **数据库迁移** - 添加 group 关联和新的 schema 格式
2. **Field Schema Editor** - 创建/编辑 Feature Group 的界面
3. **Extraction Table View** - Excel-like 的数据表格视图
4. **导出功能** - 生成 Excel/CSV 报告

我可以立即开始实现任何一个部分！🚀
