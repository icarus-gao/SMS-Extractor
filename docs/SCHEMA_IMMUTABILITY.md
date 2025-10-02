# Schema Immutability Design Summary

## 🎯 核心决策

**Schema 不可变性（Immutability）**
- Schema 一旦被使用（关联到 Project 或用于提取数据），即自动锁定
- 锁定后的 Schema 不可修改、不可删除
- 需要修改时，必须复制创建新版本

---

## ✅ 优势

### 1. 数据一致性
```
所有使用同一 Schema 提取的数据，字段结构完全一致
→ 可以安全地合并、对比、导出
→ 不会出现"部分数据有某些字段，部分没有"的情况
```

### 2. 可追溯性
```
任何时候都可以准确知道：
- 这条数据是用哪个 Schema 提取的
- Schema 的定义是什么
- AI 使用的 Prompt 是什么
→ 数据的来源清晰透明
```

### 3. 简化设计
```
不需要：
❌ 复杂的版本控制系统
❌ Schema 变更历史
❌ 数据迁移工具
❌ 兼容性检查

只需要：
✅ 锁定标志 (is_locked)
✅ 复制功能 (duplicate)
✅ 父 Schema 引用 (parent_schema)
```

### 4. 避免错误
```
防止意外修改：
- 删除了已使用的字段 → 旧数据无法显示
- 修改字段类型 → 数据验证失败
- 修改 AI Prompt → 新旧数据提取逻辑不一致
```

---

## 🔄 工作流

### 场景 1: 首次创建和使用

```
1. 创建 Schema
   User → [Create Schema] → "ML Methods v1"
   Status: Draft (Unlocked)
   
2. 设计字段
   Add fields: Method, Dataset, Accuracy
   Edit AI prompts
   Save
   
3. 应用到 Project
   Project A → [Apply Schema] → "ML Methods v1"
   → Schema 自动锁定 (is_locked = True)
   
4. 提取数据
   Run AI extraction on 20 papers
   → 生成 20 条 Extractions
   
5. Schema 现在已锁定
   Cannot edit, cannot delete
   Can: View, Use, Duplicate
```

### 场景 2: 需要修改 Schema

```
Current State:
- "ML Methods v1" 已被使用
- 有 20 条提取数据
- 现在想添加 "Training Time" 字段

操作流程:
1. 在 Schema Library 中找到 "ML Methods v1"
2. 点击 [Duplicate]
3. 输入新名称 "ML Methods v2"
4. 系统复制所有字段 → 创建 v2 (Unlocked)
5. 在 v2 中添加 "Training Time" 字段
6. Save v2

选项 A: 在新 Project 中使用 v2
  - Project B → Apply "ML Methods v2"
  - 提取新的论文

选项 B: 对已有论文重新提取
  - Project A → Apply "ML Methods v2" (作为第二个 Schema)
  - 重新运行提取 → 生成新的 20 条 Extractions
  - 现在有两个数据表：
    * v1 的表（Method, Dataset, Accuracy）
    * v2 的表（Method, Dataset, Accuracy, Training Time）
```

### 场景 3: 基于模板创建

```
1. 浏览 Schema Library
2. 找到 "ML Methods Template" (官方模板)
3. 点击 [Use as Template]
4. 系统复制模板 → 创建 "My ML Analysis" (Unlocked)
5. 自定义：
   - 保留需要的字段
   - 删除不需要的字段
   - 添加自定义字段
6. Save

优势：
- 标准化的起点
- 快速创建
- 基于最佳实践
```

---

## 🗄️ 数据库实现

### Schema 模型关键字段

```python
class Schema(models.Model):
    schema_id = CharField(primary_key=True)
    name = CharField()
    fields_definition = TextField()  # JSON, immutable
    
    # 状态控制
    is_locked = BooleanField(default=False)  # 关键！
    
    # 继承关系
    parent_schema = ForeignKey('self', null=True)  # 复制来源
    
    # 统计
    usage_count = IntegerField(default=0)
    extraction_count = IntegerField(default=0)
    
    def can_edit(self):
        return not self.is_locked
    
    def can_delete(self):
        return self.usage_count == 0 and self.extraction_count == 0
    
    def lock(self):
        """首次使用时自动调用"""
        self.is_locked = True
        self.save()
```

### 触发锁定的时机

```python
# 时机 1: Project 关联 Schema
class ProjectSchema(models.Model):
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.schema.is_locked:
            self.schema.lock()  # 自动锁定

# 时机 2: 首次创建 Extraction
class Extraction(models.Model):
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.schema.is_locked:
            self.schema.lock()  # 自动锁定
        self.schema.extraction_count += 1
        self.schema.save()
```

---

## 🎨 UI 状态标识

### Schema 状态徽章

```
📝 Draft (Unlocked)
- 绿色徽章
- "Can Edit" 提示
- 显示 [Edit] [Delete] 按钮

🔒 Locked (In Use)
- 灰色/蓝色徽章
- "In Use - Cannot Edit" 提示
- 显示 [Duplicate] 按钮
- 隐藏 [Edit] [Delete] 按钮
```

### 操作按钮逻辑

```javascript
// Schema Card 组件
function SchemaCard({ schema }) {
  const canEdit = !schema.is_locked;
  const canDelete = schema.usage_count === 0 && schema.extraction_count === 0;
  
  return (
    <div className="schema-card">
      <div className="status-badge">
        {schema.is_locked ? (
          <span className="badge-locked">🔒 Locked (In Use)</span>
        ) : (
          <span className="badge-draft">📝 Draft</span>
        )}
      </div>
      
      <div className="actions">
        <button>Preview</button>
        <button>Use in Project</button>
        <button>Duplicate</button>
        
        {canEdit && <button>Edit</button>}
        {canDelete && <button>Delete</button>}
      </div>
    </div>
  );
}
```

---

## 🚫 禁止的操作

### 锁定后不可进行的操作

```
Schema 已锁定时，以下操作会被拒绝：

1. 修改字段
   ❌ 添加新字段
   ❌ 删除现有字段
   ❌ 修改字段类型
   ❌ 修改字段名称
   ❌ 修改验证规则

2. 修改 AI 配置
   ❌ 修改 AI Prompt
   ❌ 修改提取策略
   ❌ 修改置信度阈值

3. 修改元数据
   ❌ 修改 Schema Name（部分允许）
   ❌ 修改 Category

4. 删除
   ❌ 删除整个 Schema
   ❌ 解除与 Project 的关联（如果有 Extraction）

UI 响应：
- 显示错误提示
- 建议用户使用 [Duplicate] 功能
```

### 错误提示示例

```
┌─────────────────────────────────────────────┐
│ ⚠️ Cannot Edit Locked Schema                │
├─────────────────────────────────────────────┤
│                                             │
│ This schema is currently in use and cannot  │
│ be modified to preserve data consistency.   │
│                                             │
│ Used in:                                    │
│ • 2 projects                                │
│ • 45 extractions completed                  │
│                                             │
│ To make changes:                            │
│ 1. Duplicate this schema                    │
│ 2. Modify the duplicate                     │
│ 3. Use the new version in future projects   │
│                                             │
│      [Cancel]  [Duplicate Schema]           │
└─────────────────────────────────────────────┘
```

---

## 📊 统计和追踪

### Schema 使用统计

```python
class SchemaStats:
    """Schema 使用统计"""
    
    @classmethod
    def get_stats(cls, schema):
        return {
            'usage_count': schema.usage_count,  # 被多少个 Project 使用
            'extraction_count': schema.extraction_count,  # 总提取数
            'projects': Project.objects.filter(
                project_schemas__schema=schema
            ).distinct(),
            'recent_extractions': Extraction.objects.filter(
                schema=schema
            ).order_by('-created_at')[:10],
            'derived_schemas': schema.derived_schemas.all(),  # 衍生版本
        }
```

### Schema 家族树

```
展示 Schema 的演化历史：

ML Methods Template (Official)
├─ ML Methods v1 (by User A)
│  └─ ML Methods v2 (by User A)
│     └─ ML Methods v3 (by User A)
│
└─ My Custom ML Analysis (by User B)
   └─ My Custom ML v2 (by User B)

用途：
- 追踪 Schema 的演化
- 发现相似的 Schemas
- 建议用户使用最新版本
```

---

## 🎓 用户教育

### 首次使用提示

```
┌─────────────────────────────────────────────────────┐
│ 💡 About Schema Locking                             │
├─────────────────────────────────────────────────────┤
│                                                     │
│ To ensure data consistency, schemas are            │
│ automatically locked when first used.               │
│                                                     │
│ What does this mean?                                │
│                                                     │
│ ✓ Before use: You can freely edit the schema       │
│                                                     │
│ ✓ After use: Schema is locked to protect your data │
│   • All extractions use the same structure          │
│   • Data remains consistent and exportable          │
│   • To make changes, duplicate the schema           │
│                                                     │
│ This ensures your research data stays reliable!     │
│                                                     │
│ [☑ Don't show this again]            [Got it!]     │
└─────────────────────────────────────────────────────┘
```

### Schema Editor 警告

```
Create New Schema

[Schema ID] [ml_methods_v1                          ]
[Name]      [ML Methods Comparison                  ]

Fields (3):
1. Method Name (text) *
2. Dataset (text) *  
3. Accuracy (number)

⚠️ Important: Once you use this schema in a project,
it will be locked and cannot be edited. Make sure
your field definitions are correct before proceeding.

Tip: You can always duplicate a schema to create a
modified version later.

                               [Cancel]  [Save Schema]
```

---

## 🔮 未来扩展（可选）

### 1. Schema 版本建议

```
当用户使用旧版本 Schema 时提示：

┌─────────────────────────────────────────────┐
│ ℹ️ Newer Version Available                  │
├─────────────────────────────────────────────┤
│ You are using: ML Methods v1                │
│ Latest version: ML Methods v3               │
│                                             │
│ Changes in v3:                              │
│ • Added "Training Time" field               │
│ • Improved AI prompts for accuracy          │
│                                             │
│ [Continue with v1]  [Switch to v3]          │
└─────────────────────────────────────────────┘
```

### 2. Schema 快照（Snapshot）

```python
# 在 Extraction 中保存 Schema 快照
class Extraction(models.Model):
    schema = ForeignKey(Schema)
    schema_snapshot = TextField()  # Schema 定义的完整副本
    
    def save(self, *args, **kwargs):
        # 保存当前 Schema 定义
        self.schema_snapshot = self.schema.fields_definition
        super().save(*args, **kwargs)
```

这样即使 Schema 被意外删除，Extraction 仍然保留完整定义。

### 3. Schema 归档

```python
class Schema(models.Model):
    is_archived = BooleanField(default=False)
    
    def archive(self):
        """归档不再使用的 Schema"""
        if self.usage_count == 0:
            self.is_archived = True
            self.save()
```

---

## ✅ 总结

**Schema 不可变性设计的核心价值：**

1. **简单** - 不需要复杂的版本控制
2. **安全** - 防止意外修改破坏数据
3. **一致** - 保证数据结构的统一性
4. **灵活** - 通过复制实现演化
5. **可靠** - 数据来源清晰可追溯

这个设计在简单性和功能性之间取得了良好的平衡。
