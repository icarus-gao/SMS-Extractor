# Schema 自定义功能使用指南

## 📋 功能概述

Schema Library 是 SMS Extractor 的核心功能，允许您创建、管理和使用自定义的数据提取模板。通过 Schema，您可以定义结构化字段来从论文中提取信息，并导出为 Excel、CSV 或 LaTeX 表格。

## 🎯 核心概念

### 什么是 Schema？

Schema 是一个数据提取模板，定义了：
- **字段列表**：要从论文中提取的信息（如方法名称、数据集、准确率等）
- **字段类型**：文本、数字、选择、日期等
- **验证规则**：最大长度、数值范围等
- **AI 提取配置**：如何使用 AI 自动提取数据
- **导出配置**：如何在 Excel 中显示（列名、宽度、对齐等）

### Schema 生命周期

```
📝 Draft (草稿) ──首次使用──> 🔒 Locked (锁定)
                                      │
                                      │ 需要修改？
                                      ▼
                                   复制 ──> 📝 New Draft
```

- **Draft 状态**：可以自由编辑和删除
- **Locked 状态**：不可编辑，确保数据一致性
- **自动锁定**：当 Schema 首次被项目使用时自动锁定
- **演进方式**：复制现有 Schema 创建新版本

## 🚀 快速开始

### 1. 访问 Schema Library

打开浏览器访问：
```
http://127.0.0.1:8000/projects/schemas/
```

或通过左侧导航栏点击 **"Schema Library"**。

### 2. 查看示例 Schema

系统已预装两个示例 Schema：

1. **ML Methods Comparison** (机器学习方法对比)
   - 用于对比不同机器学习方法
   - 包含：方法名称、数据集、准确率、模型类型等字段

2. **Study Characteristics** (研究特征提取)
   - 用于系统性文献综述
   - 包含：研究设计、样本量、干预措施、结局指标等字段

### 3. 创建您的第一个 Schema

#### 方法一：复制示例 Schema

1. 在 Schema Library 中找到示例 Schema
2. 点击卡片底部的 **"复制"** 图标
3. 输入新名称，点击 **"复制"**
4. 在新 Schema 中修改字段定义

#### 方法二：从头创建

1. 点击右上角 **"创建新 Schema"** 按钮
2. 填写基本信息：
   - **Schema 名称**：英文名称（必填）
   - **中文名称**：可选，方便理解
   - **分类**：如 "Machine Learning", "Healthcare" 等
   - **描述**：简要说明用途

3. 编辑 JSON 定义（右侧编辑器）

## 📝 Schema JSON 格式

### 基本结构

```json
{
  "schema_meta": {
    "name": "Your Schema Name",
    "description": "Schema description",
    "category": "Category",
    "version": "1.0"
  },
  "export_config": {
    "default_format": "excel",
    "include_metadata": true,
    "include_confidence": false
  },
  "fields": [
    // 字段定义列表
  ]
}
```

### 字段定义示例

#### 1. 文本字段（text）

```json
{
  "field_id": "method_name",
  "order": 1,
  "name": "Method Name",
  "name_zh": "方法名称",
  "type": "text",
  "description": "Name of the ML method",
  "placeholder": "e.g., CNN, LSTM",
  "required": true,
  "validation": {
    "max_length": 100
  },
  "extraction": {
    "mode": "ai",
    "allow_manual": true,
    "prompt": "What is the method name?",
    "strategy": "semantic_search",
    "confidence_threshold": 0.7
  },
  "export": {
    "enabled": true,
    "column_name": "Method",
    "width": 150,
    "align": "left"
  }
}
```

#### 2. 数字字段（number）

```json
{
  "field_id": "accuracy",
  "order": 2,
  "name": "Accuracy",
  "type": "number",
  "description": "Model accuracy (%)",
  "required": false,
  "validation": {
    "min": 0,
    "max": 100,
    "decimal_places": 2
  },
  "unit": "%",
  "extraction": {
    "mode": "ai",
    "prompt": "What is the accuracy?"
  },
  "export": {
    "enabled": true,
    "column_name": "Accuracy (%)",
    "width": 100,
    "align": "right",
    "format": "0.00"
  }
}
```

#### 3. 单选字段（select）

```json
{
  "field_id": "model_type",
  "order": 3,
  "name": "Model Type",
  "type": "select",
  "required": true,
  "options": [
    {"value": "cnn", "label": "CNN"},
    {"value": "rnn", "label": "RNN"},
    {"value": "lstm", "label": "LSTM"},
    {"value": "transformer", "label": "Transformer"}
  ],
  "extraction": {
    "mode": "ai",
    "prompt": "What type of model is used?"
  },
  "export": {
    "enabled": true,
    "column_name": "Type",
    "width": 120,
    "align": "left"
  }
}
```

#### 4. 多选字段（multi-select）

```json
{
  "field_id": "domains",
  "order": 4,
  "name": "Application Domains",
  "type": "multi-select",
  "required": false,
  "options": [
    {"value": "cv", "label": "Computer Vision"},
    {"value": "nlp", "label": "NLP"},
    {"value": "speech", "label": "Speech Recognition"}
  ],
  "extraction": {
    "mode": "ai",
    "prompt": "What domains is this method used for?"
  },
  "export": {
    "enabled": true,
    "column_name": "Domains",
    "width": 150,
    "align": "left",
    "format": "comma_separated"
  }
}
```

#### 5. 布尔字段（boolean）

```json
{
  "field_id": "code_available",
  "order": 5,
  "name": "Code Available",
  "type": "boolean",
  "required": false,
  "extraction": {
    "mode": "ai",
    "prompt": "Is source code available?"
  },
  "export": {
    "enabled": true,
    "column_name": "Code",
    "width": 80,
    "align": "center",
    "format": "yes_no"
  }
}
```

#### 6. 长文本字段（long-text）

```json
{
  "field_id": "strengths",
  "order": 6,
  "name": "Strengths",
  "type": "long-text",
  "description": "Main strengths of the method",
  "required": false,
  "validation": {
    "max_length": 1000
  },
  "extraction": {
    "mode": "ai",
    "prompt": "What are the main strengths?"
  },
  "export": {
    "enabled": true,
    "column_name": "Strengths",
    "width": 300,
    "align": "left",
    "format": "wrap_text"
  }
}
```

#### 7. 系统字段（auto）

```json
{
  "field_id": "paper_id",
  "order": 1,
  "name": "Paper ID",
  "type": "auto",
  "description": "Automatically filled",
  "required": true,
  "system_field": true,
  "export": {
    "enabled": true,
    "column_name": "ID",
    "width": 80,
    "align": "left"
  }
}
```

### 支持的字段类型

| 类型 | 说明 | 用途 |
|------|------|------|
| `text` | 短文本 | 名称、标题等 |
| `long-text` | 长文本 | 摘要、描述等 |
| `number` | 数字 | 准确率、样本量等 |
| `select` | 单选 | 类别选择 |
| `multi-select` | 多选 | 多个类别 |
| `boolean` | 是/否 | 二元判断 |
| `date` | 日期 | 完整日期 |
| `year` | 年份 | 仅年份 |
| `url` | 网址 | 链接地址 |
| `rating` | 评分 | 质量评分等 |
| `multi-text` | 多行文本 | 列表项 |
| `auto` | 系统自动 | Paper ID、Citation 等 |

## 🔧 编辑器功能

### JSON 编辑器工具栏

- **格式化**：自动格式化 JSON（Ctrl+Shift+F）
- **验证**：检查 JSON 格式和 Schema 结构
- **加载模板**：快速插入标准模板

### 自动保存

编辑器会自动将内容保存到浏览器本地存储，防止意外丢失。

## 📊 导出配置

### Excel 导出设置

```json
"export": {
  "enabled": true,           // 是否导出此字段
  "column_name": "Method",   // Excel 列名
  "width": 150,              // 列宽（像素）
  "align": "left",           // 对齐方式：left/center/right
  "format": "0.00"           // 数字格式
}
```

### 特殊格式

- **数字格式**：`"0.00"`, `"#,##0"`, `"0.0%"` 等
- **文本换行**：`"format": "wrap_text"`
- **是/否显示**：`"format": "yes_no"`
- **逗号分隔**：`"format": "comma_separated"`（用于多选）

## 🎨 最佳实践

### 1. 命名规范

- **field_id**：使用小写和下划线，如 `method_name`
- **name**：使用简洁的英文名称，如 `"Method Name"`
- **name_zh**：添加中文名便于理解

### 2. 字段顺序

使用 `order` 字段控制显示顺序：
- 系统字段（paper_id, citation_key）：1-2
- 核心字段：3-10
- 补充字段：11+

### 3. 必填字段

只将真正必需的字段设为 `required: true`，保持灵活性。

### 4. AI 提取配置

- **清晰的 prompt**：准确描述要提取的信息
- **合适的置信度**：0.7-0.8 是好的起点
- **允许手动修改**：设置 `allow_manual: true`

### 5. 验证规则

添加合理的验证：
```json
"validation": {
  "max_length": 200,    // 文本最大长度
  "min": 0,             // 数字最小值
  "max": 100,           // 数字最大值
  "decimal_places": 2   // 小数位数
}
```

## 🔄 Schema 管理

### 查看 Schema

- 点击 Schema 卡片查看详细信息
- 查看字段列表、使用的项目、元数据等

### 编辑 Schema

⚠️ **只能编辑 Draft 状态的 Schema**

1. 打开 Schema 详情页
2. 点击 **"编辑"** 按钮
3. 修改内容后点击 **"保存"**

### 复制 Schema

适用于：
- 创建类似的 Schema
- 对 Locked Schema 进行修改

步骤：
1. 点击 **"复制"** 按钮
2. 输入新名称
3. 在新 Schema 中进行修改

### 锁定 Schema

两种锁定方式：
1. **自动锁定**：首次被项目使用时
2. **手动锁定**：确定不再修改时主动锁定

⚠️ 锁定后无法撤销！

### 删除 Schema

条件：
- 必须是 Draft 状态
- 没有被任何项目使用

## 🔍 搜索和筛选

### 搜索

支持搜索：
- Schema 名称（英文和中文）
- Schema ID
- 描述文字

### 筛选

- **分类筛选**：按 Category 筛选
- **状态筛选**：Draft / Locked

## 📈 使用统计

每个 Schema 显示：
- **字段数量**：定义的字段总数
- **项目使用**：有多少项目在使用
- **提取次数**：总共进行了多少次数据提取

## 🐛 常见问题

### Q: JSON 验证失败？

**A**: 检查以下常见错误：
- 缺少必填字段：`field_id`, `name`, `type`, `order`
- JSON 格式错误：缺少逗号、引号不匹配等
- 使用格式化工具自动修复

### Q: 为什么无法编辑 Schema？

**A**: Schema 可能已被锁定。检查：
- 是否被项目使用（自动锁定）
- 是否手动锁定
- 解决方法：复制一个新的 Schema 进行修改

### Q: 如何修改已锁定的 Schema？

**A**: 不能直接修改，但可以：
1. 复制该 Schema
2. 在新 Schema 中进行修改
3. 将新 Schema 关联到项目

### Q: 可以删除被使用的 Schema 吗？

**A**: 不可以。必须先：
1. 移除所有项目的关联
2. 确保没有提取记录
3. 然后才能删除

## 📚 进阶功能

### 条件格式（未来版本）

在 export 配置中添加条件格式：

```json
"export": {
  "style": {
    "conditional_formatting": [
      {"condition": ">= 95", "color": "#d4edda"},
      {"condition": ">= 90", "color": "#fff3cd"},
      {"condition": "< 90", "color": "#f8d7da"}
    ]
  }
}
```

### AI 提取策略

不同的提取策略适用于不同场景：

- `semantic_search`：语义搜索，适用于概念提取
- `full_text`：全文搜索，适用于关键词提取
- `table_extraction`：表格提取，适用于结构化数据
- `classification`：分类，适用于选择题

## 🎓 示例场景

### 场景 1：机器学习论文对比

使用 **ML Methods Comparison** Schema 提取：
- 方法名称
- 使用的数据集
- 准确率/性能指标
- 模型架构
- 优缺点

### 场景 2：系统性文献综述

使用 **Study Characteristics** Schema 提取：
- 研究设计类型
- 样本量
- 干预措施
- 结局指标
- 研究质量

### 场景 3：自定义场景

根据您的需求创建专门的 Schema：
- 用户体验研究
- 安全漏洞分析
- 金融风险评估
- 医疗诊断标准
- ...任何结构化数据提取需求

## 🚀 下一步

1. **创建您的第一个 Schema**
2. **将 Schema 关联到项目**（即将推出）
3. **使用 AI 提取数据**（即将推出）
4. **导出为 Excel 表格**（即将推出）

## 📞 获取帮助

- 查看 [SCHEMA_DESIGN.md](./SCHEMA_DESIGN.md) 了解完整设计文档
- 查看 [SCHEMA_EXPORT_IMPLEMENTATION.md](./SCHEMA_EXPORT_IMPLEMENTATION.md) 了解导出功能
- 参考示例 Schema 学习最佳实践

---

**提示**：Schema Library 是一个强大且灵活的工具，花时间设计好您的 Schema 将大大提高数据提取的效率和质量！
