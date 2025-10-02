"""
测试 Schema 功能的关键部分
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sms_backend.settings')
django.setup()

from projects.models import Schema, ProjectSchema, Project
import json


def test_schema_creation():
    """测试 Schema 创建"""
    print("=" * 60)
    print("测试 1: Schema 创建")
    print("=" * 60)
    
    # 创建测试 Schema
    fields_def = {
        "schema_meta": {
            "name": "Test Schema",
            "version": "1.0"
        },
        "fields": [
            {
                "field_id": "test_field",
                "name": "Test Field",
                "type": "text",
                "required": True
            }
        ]
    }
    
    try:
        schema = Schema.objects.create(
            name="Test Schema",
            description="Test description",
            fields_definition=json.dumps(fields_def),
        )
        print(f"✅ Schema 创建成功: {schema.schema_id}")
        print(f"   状态: {'🔒 Locked' if schema.is_locked else '📝 Draft'}")
        print(f"   字段数量: {len(schema.get_fields())}")
        return schema
    except Exception as e:
        print(f"❌ Schema 创建失败: {str(e)}")
        return None


def test_schema_locking(schema):
    """测试 Schema 锁定机制"""
    print("\n" + "=" * 60)
    print("测试 2: Schema 锁定机制")
    print("=" * 60)
    
    if not schema:
        print("⚠️  跳过测试（需要先创建 Schema）")
        return
    
    print(f"初始状态: can_edit={schema.can_edit()}, is_locked={schema.is_locked}")
    
    # 锁定 Schema
    schema.lock()
    schema.refresh_from_db()
    
    print(f"锁定后: can_edit={schema.can_edit()}, is_locked={schema.is_locked}")
    
    if schema.is_locked and not schema.can_edit():
        print("✅ 锁定机制正常工作")
    else:
        print("❌ 锁定机制异常")


def test_schema_duplication(schema):
    """测试 Schema 复制"""
    print("\n" + "=" * 60)
    print("测试 3: Schema 复制")
    print("=" * 60)
    
    if not schema:
        print("⚠️  跳过测试（需要先创建 Schema）")
        return None
    
    try:
        new_schema = schema.duplicate(new_name="Test Schema Copy")
        print(f"✅ Schema 复制成功: {new_schema.schema_id}")
        print(f"   原 Schema: {schema.schema_id} (v{schema.version})")
        print(f"   新 Schema: {new_schema.schema_id} (v{new_schema.version})")
        print(f"   父 Schema: {new_schema.parent_schema.schema_id if new_schema.parent_schema else 'None'}")
        return new_schema
    except Exception as e:
        print(f"❌ Schema 复制失败: {str(e)}")
        return None


def test_get_fields(schema):
    """测试字段获取"""
    print("\n" + "=" * 60)
    print("测试 4: 字段获取")
    print("=" * 60)
    
    if not schema:
        print("⚠️  跳过测试（需要先创建 Schema）")
        return
    
    try:
        fields = schema.get_fields()
        print(f"✅ 字段获取成功: {len(fields)} 个字段")
        for field in fields:
            print(f"   - {field.get('name')}: {field.get('type')}")
    except Exception as e:
        print(f"❌ 字段获取失败: {str(e)}")


def test_project_schema_association():
    """测试项目与 Schema 的关联"""
    print("\n" + "=" * 60)
    print("测试 5: 项目-Schema 关联")
    print("=" * 60)
    
    # 查找现有的项目和 Schema
    project = Project.objects.first()
    schema = Schema.objects.filter(is_locked=False).first()
    
    if not project:
        print("⚠️  没有找到项目，跳过测试")
        return
    
    if not schema:
        print("⚠️  没有找到 Draft Schema，跳过测试")
        return
    
    try:
        # 创建关联
        project_schema, created = ProjectSchema.objects.get_or_create(
            project=project,
            schema=schema
        )
        
        if created:
            print(f"✅ 关联创建成功")
        else:
            print(f"ℹ️  关联已存在")
        
        print(f"   项目: {project.project_id}")
        print(f"   Schema: {schema.schema_id}")
        print(f"   Schema 状态: {'🔒 Locked' if schema.is_locked else '📝 Draft'}")
        
        # 检查 Schema 是否被自动锁定
        schema.refresh_from_db()
        if schema.is_locked:
            print("✅ Schema 自动锁定成功")
        else:
            print("⚠️  Schema 未被自动锁定（预期行为可能不同）")
        
    except Exception as e:
        print(f"❌ 关联失败: {str(e)}")


def test_json_parsing():
    """测试 JSON 解析的错误处理"""
    print("\n" + "=" * 60)
    print("测试 6: JSON 解析错误处理")
    print("=" * 60)
    
    # 创建一个带有错误 JSON 的 Schema
    try:
        schema = Schema(
            name="Bad JSON Test",
            fields_definition="invalid json {{{",
        )
        schema.save()
        
        # 测试 get_fields 是否安全返回空列表
        fields = schema.get_fields()
        
        if fields == []:
            print("✅ 错误 JSON 处理正确（返回空列表）")
        else:
            print(f"⚠️  意外返回: {fields}")
        
        # 清理
        schema.delete()
        
    except Exception as e:
        print(f"❌ JSON 错误处理失败: {str(e)}")


def cleanup_test_data():
    """清理测试数据"""
    print("\n" + "=" * 60)
    print("清理测试数据")
    print("=" * 60)
    
    try:
        # 删除测试创建的 Schema
        deleted = Schema.objects.filter(name__startswith="Test Schema").delete()
        print(f"✅ 清理完成: 删除了 {deleted[0]} 个对象")
    except Exception as e:
        print(f"❌ 清理失败: {str(e)}")


def main():
    print("\n" + "🔬" * 30)
    print("开始测试 Schema 功能")
    print("🔬" * 30 + "\n")
    
    # 运行测试
    schema = test_schema_creation()
    test_get_fields(schema)
    test_schema_locking(schema)
    duplicate = test_schema_duplication(schema)
    test_project_schema_association()
    test_json_parsing()
    
    # 清理
    cleanup_test_data()
    
    print("\n" + "✨" * 30)
    print("测试完成")
    print("✨" * 30 + "\n")


if __name__ == "__main__":
    main()
