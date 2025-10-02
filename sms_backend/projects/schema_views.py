"""Schema 相关的视图函数"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.db.models import Q
import json
import time

from .models import Schema, ProjectSchema, Project


def schema_library(request):
    """Schema Library - 显示所有可用的 Schema"""
    
    # 搜索和筛选
    search_query = request.GET.get('q', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')  # all, draft, locked
    
    schemas = Schema.objects.all()
    
    # 应用搜索
    if search_query:
        schemas = schemas.filter(
            Q(name__icontains=search_query) |
            Q(name_zh__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(schema_id__icontains=search_query)
        )
    
    # 应用分类筛选
    if category_filter:
        schemas = schemas.filter(category=category_filter)
    
    # 应用状态筛选
    if status_filter == 'draft':
        schemas = schemas.filter(is_locked=False)
    elif status_filter == 'locked':
        schemas = schemas.filter(is_locked=True)
    
    # 获取所有分类（用于筛选器）
    categories = Schema.objects.values_list('category', flat=True).distinct()
    categories = [c for c in categories if c]
    
    context = {
        'schemas': schemas,
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'categories': categories,
    }
    
    return render(request, 'projects/schema_library.html', context)


def schema_detail(request, schema_id):
    """Schema 详情页"""
    schema = get_object_or_404(Schema, schema_id=schema_id)
    
    # 获取使用该 Schema 的项目
    projects_using = Project.objects.filter(
        project_schemas__schema=schema
    ).distinct()
    
    # 解析字段定义
    try:
        fields_definition = json.loads(schema.fields_definition)
    except:
        fields_definition = {}
    
    context = {
        'schema': schema,
        'projects_using': projects_using,
        'fields_definition': fields_definition,
        'fields': schema.get_fields(),
    }
    
    return render(request, 'projects/schema_detail.html', context)


@require_http_methods(["GET", "POST"])
def schema_create(request):
    """创建新 Schema"""
    
    if request.method == "POST":
        try:
            name = request.POST.get('name')
            name_zh = request.POST.get('name_zh', '')
            description = request.POST.get('description', '')
            category = request.POST.get('category', '')
            
            # 获取字段定义（从表单或 JSON）
            if 'fields_json' in request.POST:
                fields_definition = request.POST.get('fields_json')
                # 验证 JSON 格式
                json.loads(fields_definition)
            else:
                # 如果没有提供 JSON，创建一个空的模板
                fields_definition = json.dumps({
                    "schema_meta": {
                        "name": name,
                        "description": description,
                        "category": category,
                        "version": "1.0",
                    },
                    "export_config": {
                        "default_format": "excel",
                        "include_metadata": True,
                        "include_confidence": False,
                    },
                    "fields": []
                }, ensure_ascii=False, indent=2)
            
            # 创建 Schema
            schema = Schema.objects.create(
                name=name,
                name_zh=name_zh,
                description=description,
                category=category,
                fields_definition=fields_definition,
                created_by=request.user.username if request.user.is_authenticated else None,
            )
            
            messages.success(request, f'Schema "{schema.name}" 创建成功！')
            return redirect('schema_edit', schema_id=schema.schema_id)
            
        except json.JSONDecodeError:
            messages.error(request, '字段定义 JSON 格式错误，请检查！')
        except Exception as e:
            messages.error(request, f'创建 Schema 失败: {str(e)}')
    
    # GET 请求 - 显示创建表单
    context = {
        'mode': 'create',
    }
    return render(request, 'projects/schema_form.html', context)


@require_http_methods(["GET", "POST"])
def schema_edit(request, schema_id):
    """编辑 Schema（仅 Draft 状态）"""
    schema = get_object_or_404(Schema, schema_id=schema_id)
    
    # 检查是否可以编辑
    if schema.is_locked:
        messages.warning(request, '该 Schema 已锁定，无法编辑。您可以复制一个新的 Schema 进行修改。')
        return redirect('schema_detail', schema_id=schema_id)
    
    if request.method == "POST":
        try:
            schema.name = request.POST.get('name', schema.name)
            schema.name_zh = request.POST.get('name_zh', schema.name_zh)
            schema.description = request.POST.get('description', schema.description)
            schema.category = request.POST.get('category', schema.category)
            
            # 更新字段定义
            if 'fields_json' in request.POST:
                fields_definition = request.POST.get('fields_json')
                # 验证 JSON 格式
                json.loads(fields_definition)
                schema.fields_definition = fields_definition
            
            schema.save()
            
            messages.success(request, f'Schema "{schema.name}" 更新成功！')
            return redirect('schema_detail', schema_id=schema.schema_id)
            
        except json.JSONDecodeError:
            messages.error(request, '字段定义 JSON 格式错误，请检查！')
        except Exception as e:
            messages.error(request, f'更新 Schema 失败: {str(e)}')
    
    # GET 请求 - 显示编辑表单
    context = {
        'mode': 'edit',
        'schema': schema,
        'fields_json': schema.fields_definition,
    }
    return render(request, 'projects/schema_form.html', context)


@require_POST
def schema_delete(request, schema_id):
    """删除 Schema（仅未使用的 Draft）"""
    schema = get_object_or_404(Schema, schema_id=schema_id)
    
    if not schema.can_delete():
        if schema.is_locked:
            messages.error(request, '无法删除已锁定的 Schema！')
        else:
            messages.error(request, f'该 Schema 已被 {schema.usage_count} 个项目使用，无法删除！')
        return redirect('schema_detail', schema_id=schema_id)
    
    schema_name = schema.name
    schema.delete()
    
    messages.success(request, f'Schema "{schema_name}" 已删除！')
    return redirect('schema_library')


@require_POST
def schema_duplicate(request, schema_id):
    """复制 Schema"""
    original_schema = get_object_or_404(Schema, schema_id=schema_id)
    
    try:
        new_name = request.POST.get('new_name', f"{original_schema.name} (Copy)")
        created_by = request.user.username if request.user.is_authenticated else None
        
        new_schema = original_schema.duplicate(
            new_name=new_name,
            created_by=created_by
        )
        
        messages.success(request, f'Schema "{new_schema.name}" 已创建！')
        return redirect('schema_edit', schema_id=new_schema.schema_id)
        
    except Exception as e:
        messages.error(request, f'复制 Schema 失败: {str(e)}')
        return redirect('schema_detail', schema_id=schema_id)


@require_POST
def schema_lock(request, schema_id):
    """手动锁定 Schema"""
    schema = get_object_or_404(Schema, schema_id=schema_id)
    
    if schema.is_locked:
        messages.warning(request, '该 Schema 已经是锁定状态！')
    else:
        schema.lock()
        messages.success(request, f'Schema "{schema.name}" 已锁定！')
    
    return redirect('schema_detail', schema_id=schema_id)


# ==================== API Views (JSON Response) ====================

def schema_fields_api(request, schema_id):
    """API: 获取 Schema 的字段列表（JSON）"""
    schema = get_object_or_404(Schema, schema_id=schema_id)
    
    try:
        fields_definition = json.loads(schema.fields_definition)
        fields = fields_definition.get('fields', [])
        
        return JsonResponse({
            'success': True,
            'schema_id': schema.schema_id,
            'schema_name': schema.name,
            'is_locked': schema.is_locked,
            'fields': fields,
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def schema_validate_api(request):
    """API: 验证 Schema JSON 格式"""
    if request.method == "POST":
        try:
            fields_json = request.POST.get('fields_json', '')
            fields_definition = json.loads(fields_json)
            
            # 基本验证
            errors = []
            
            # 必须包含 fields 数组
            if 'fields' not in fields_definition:
                errors.append('缺少 "fields" 数组')
            else:
                fields = fields_definition['fields']
                if not isinstance(fields, list):
                    errors.append('"fields" 必须是数组')
                else:
                    # 验证每个字段
                    for idx, field in enumerate(fields):
                        if 'field_id' not in field:
                            errors.append(f'字段 {idx + 1} 缺少 "field_id"')
                        if 'name' not in field:
                            errors.append(f'字段 {idx + 1} 缺少 "name"')
                        if 'type' not in field:
                            errors.append(f'字段 {idx + 1} 缺少 "type"')
            
            if errors:
                return JsonResponse({
                    'success': False,
                    'valid': False,
                    'errors': errors
                })
            else:
                return JsonResponse({
                    'success': True,
                    'valid': True,
                    'message': 'Schema 格式验证通过！'
                })
                
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'valid': False,
                'errors': [f'JSON 格式错误: {str(e)}']
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)


# ==================== Project-Schema Association ====================

@require_POST
def project_add_schema(request, project_id):
    """为项目添加 Schema"""
    project = get_object_or_404(Project, project_id=project_id)
    schema_id = request.POST.get('schema_id')
    
    if not schema_id:
        messages.error(request, '请选择一个 Schema！')
        return redirect('project_detail', project_id=project_id)
    
    schema = get_object_or_404(Schema, schema_id=schema_id)
    
    try:
        # 检查是否已关联
        if ProjectSchema.objects.filter(project=project, schema=schema).exists():
            messages.warning(request, f'项目已关联 Schema "{schema.name}"！')
        else:
            ProjectSchema.objects.create(
                project=project,
                schema=schema,
            )
            messages.success(request, f'成功为项目添加 Schema "{schema.name}"！')
            
    except Exception as e:
        messages.error(request, f'添加 Schema 失败: {str(e)}')
    
    return redirect('project_detail', project_id=project_id)


@require_POST
def project_remove_schema(request, project_id, schema_id):
    """移除项目的 Schema 关联"""
    project = get_object_or_404(Project, project_id=project_id)
    schema = get_object_or_404(Schema, schema_id=schema_id)
    
    try:
        project_schema = ProjectSchema.objects.get(project=project, schema=schema)
        
        # 检查是否有相关的 extractions
        extraction_count = project.extractions.filter(schema=schema).count()
        if extraction_count > 0:
            messages.error(request, f'无法移除！该 Schema 已有 {extraction_count} 条提取记录。')
            return redirect('project_detail', project_id=project_id)
        
        project_schema.delete()
        messages.success(request, f'已移除 Schema "{schema.name}"！')
        
    except ProjectSchema.DoesNotExist:
        messages.error(request, '该 Schema 未关联到此项目！')
    except Exception as e:
        messages.error(request, f'移除 Schema 失败: {str(e)}')
    
    return redirect('project_detail', project_id=project_id)
