"""Schema-related view functions"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.db.models import Q
import json
import time

from .models import Schema, ProjectSchema, Project


def schema_library(request):
    """Schema Library - Display all available schemas"""
    
    # Search and filter
    search_query = request.GET.get('q', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')  # all, draft, locked
    
    schemas = Schema.objects.all()
    
    # Apply search
    if search_query:
        schemas = schemas.filter(
            Q(name__icontains=search_query) |
            Q(name_zh__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(schema_id__icontains=search_query)
        )
    
    # Apply category filter
    if category_filter:
        schemas = schemas.filter(category=category_filter)
    
    # Apply status filter
    if status_filter == 'draft':
        schemas = schemas.filter(is_locked=False)
    elif status_filter == 'locked':
        schemas = schemas.filter(is_locked=True)
    
    # Get all categories (for filter)
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
    """Schema detail page"""
    schema = get_object_or_404(Schema, schema_id=schema_id)
    
    # Get projects using this schema
    projects_using = Project.objects.filter(
        project_schemas__schema=schema
    ).distinct()
    
    # Parse fields definition
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
    """Create new schema"""
    
    if request.method == "POST":
        try:
            name = request.POST.get('name')
            name_zh = request.POST.get('name_zh', '')
            description = request.POST.get('description', '')
            category = request.POST.get('category', '')
            
            # Get fields definition (from form or JSON)
            if 'fields_json' in request.POST:
                fields_definition = request.POST.get('fields_json')
                # Validate JSON format
                json.loads(fields_definition)
            else:
                # If no JSON provided, create an empty template
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
            
            # Create schema
            schema = Schema.objects.create(
                name=name,
                name_zh=name_zh,
                description=description,
                category=category,
                fields_definition=fields_definition,
                created_by=request.user.username if request.user.is_authenticated else None,
            )
            
            messages.success(request, f'Schema "{schema.name}" created successfully!')
            return redirect('dashboard:schema-edit', schema_id=schema.schema_id)
            
        except json.JSONDecodeError:
            messages.error(request, 'Invalid JSON format for fields definition!')
        except Exception as e:
            messages.error(request, f'Failed to create schema: {str(e)}')
    
    # GET request - Show create form
    context = {
        'mode': 'create',
    }
    return render(request, 'projects/schema_form.html', context)


@require_http_methods(["GET", "POST"])
def schema_edit(request, schema_id):
    """Edit schema (Draft status only)"""
    schema = get_object_or_404(Schema, schema_id=schema_id)
    
    # Check if editable
    if schema.is_locked:
        messages.warning(request, 'This schema is locked and cannot be edited. You can duplicate it to make changes.')
        return redirect('dashboard:schema-detail', schema_id=schema_id)
    
    if request.method == "POST":
        try:
            schema.name = request.POST.get('name', schema.name)
            schema.name_zh = request.POST.get('name_zh', schema.name_zh)
            schema.description = request.POST.get('description', schema.description)
            schema.category = request.POST.get('category', schema.category)
            
            # Update fields definition
            if 'fields_json' in request.POST:
                fields_definition = request.POST.get('fields_json')
                # Validate JSON format
                json.loads(fields_definition)
                schema.fields_definition = fields_definition
            
            schema.save()
            
            messages.success(request, f'Schema "{schema.name}" updated successfully!')
            return redirect('dashboard:schema-detail', schema_id=schema.schema_id)
            
        except json.JSONDecodeError:
            messages.error(request, 'Invalid JSON format for fields definition!')
        except Exception as e:
            messages.error(request, f'Failed to update schema: {str(e)}')
    
    # GET request - Show edit form
    context = {
        'mode': 'edit',
        'schema': schema,
        'fields_json': schema.fields_definition,
    }
    return render(request, 'projects/schema_form.html', context)


@require_POST
def schema_delete(request, schema_id):
    """
    Delete schema.
    If the schema is a draft (not locked), it can be deleted.
    This will also remove it from all associated projects and delete related extractions.
    """
    schema = get_object_or_404(Schema, schema_id=schema_id)
    
    if not schema.can_delete():
        messages.error(request, 'Cannot delete a locked (Published) schema!')
        return redirect('dashboard:schema-detail', schema_id=schema_id)
    
    schema_name = schema.name
    usage_count = schema.usage_count
    
    # The ManyToManyField and ForeignKey on_delete=CASCADE will handle deletion.
    schema.delete()
    
    if usage_count > 0:
        messages.success(request, f'Schema "{schema_name}" has been deleted. It was removed from {usage_count} project(s) and all related extractions were cleared.')
    else:
        messages.success(request, f'Schema "{schema_name}" was successfully deleted.')
        
    return redirect('dashboard:schema-library')


@require_POST
def schema_duplicate(request, schema_id):
    """Duplicate schema"""
    original_schema = get_object_or_404(Schema, schema_id=schema_id)
    
    try:
        new_name = request.POST.get('new_name', f"{original_schema.name} (Copy)")
        created_by = request.user.username if request.user.is_authenticated else None
        
        new_schema = original_schema.duplicate(
            new_name=new_name,
            created_by=created_by
        )
        
        messages.success(request, f'Schema "{new_schema.name}" created successfully!')
        return redirect('dashboard:schema-edit', schema_id=new_schema.schema_id)
        
    except Exception as e:
        messages.error(request, f'Failed to duplicate schema: {str(e)}')
        return redirect('dashboard:schema-detail', schema_id=schema_id)


@require_POST
def schema_lock(request, schema_id):
    """Manually lock schema"""
    schema = get_object_or_404(Schema, schema_id=schema_id)
    
    if schema.is_locked:
        messages.warning(request, 'This schema is already locked!')
    else:
        schema.lock()
        messages.success(request, f'Schema "{schema.name}" locked successfully!')
    
    return redirect('dashboard:schema-detail', schema_id=schema_id)


@require_POST
def schema_unlock(request, schema_id):
    """Manually unlock a schema, changing it back to a Draft."""
    schema = get_object_or_404(Schema, schema_id=schema_id)
    
    if not schema.is_locked:
        messages.warning(request, 'This schema is already unlocked (Draft).')
    else:
        schema.unlock()
        messages.success(request, f'Schema "{schema.name}" has been unlocked and is now a Draft. It can now be edited or deleted.')
    
    return redirect('dashboard:schema-detail', schema_id=schema_id)


# ==================== API Views (JSON Response) ====================

def schema_fields_api(request, schema_id):
    """API: Get schema field list (JSON)"""
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
    """API: Validate schema JSON format"""
    if request.method == "POST":
        try:
            fields_json = request.POST.get('fields_json', '')
            fields_definition = json.loads(fields_json)
            
            # Basic validation
            errors = []
            
            # Must contain fields array
            if 'fields' not in fields_definition:
                errors.append('Missing "fields" array')
            else:
                fields = fields_definition['fields']
                if not isinstance(fields, list):
                    errors.append('"fields" must be an array')
                else:
                    # Validate each field
                    for idx, field in enumerate(fields):
                        if 'field_id' not in field:
                            errors.append(f'Field {idx + 1} missing "field_id"')
                        if 'name' not in field:
                            errors.append(f'Field {idx + 1} missing "name"')
                        if 'type' not in field:
                            errors.append(f'Field {idx + 1} missing "type"')
            
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
                    'message': 'Schema format validation passed!'
                })
                
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'valid': False,
                'errors': [f'Invalid JSON format: {str(e)}']
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
    """Add schema to project"""
    project = get_object_or_404(Project, project_id=project_id)
    schema_id = request.POST.get('schema_id')
    
    if not schema_id:
        messages.error(request, 'Please select a schema!')
        return redirect('dashboard:project-detail', project_id=project_id)
    
    schema = get_object_or_404(Schema, schema_id=schema_id)
    
    try:
        # Check if already associated
        if ProjectSchema.objects.filter(project=project, schema=schema).exists():
            messages.warning(request, f'Schema "{schema.name}" is already added to this project!')
        else:
            ProjectSchema.objects.create(
                project=project,
                schema=schema,
            )
            messages.success(request, f'Schema "{schema.name}" added to project successfully!')
            
    except Exception as e:
        messages.error(request, f'Failed to add schema: {str(e)}')
    
    return redirect('dashboard:project-detail', project_id=project_id)


@require_POST
def project_remove_schema(request, project_id, schema_id):
    """Remove schema from project and all related extraction records"""
    project = get_object_or_404(Project, project_id=project_id)
    schema = get_object_or_404(Schema, schema_id=schema_id)
    
    try:
        project_schema = ProjectSchema.objects.get(project=project, schema=schema)
        
        # Count related extractions
        extraction_count = project.extractions.filter(schema=schema).count()
        
        # Delete all related extraction records first
        if extraction_count > 0:
            deleted_count = project.extractions.filter(schema=schema).delete()[0]
            messages.warning(request, f'Deleted {deleted_count} extraction record(s) associated with schema "{schema.name}".')
        
        # Then remove the schema from project
        project_schema.delete()
        messages.success(request, f'Schema "{schema.name}" removed from project successfully!')
        
    except ProjectSchema.DoesNotExist:
        messages.error(request, 'This schema is not associated with this project!')
    except Exception as e:
        messages.error(request, f'Failed to remove schema: {str(e)}')
    
    return redirect('dashboard:project-detail', project_id=project_id)
