"""
Django Views for SMS Extractor Dashboard
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q, Avg
from datetime import datetime, timedelta
from collections import defaultdict
import json
import os
import csv

from projects.models import Project, ProjectGroup, ProjectSchema, Schema
from papers.models import Paper
from extractions.models import Extraction

# Utility functions will be implemented later or imported correctly
def get_project_stats(project_id):
    """Get project statistics"""
    return {
        'total_papers': Paper.objects.filter(project__project_id=project_id).count(),
        'total_schemas': ProjectSchema.objects.filter(project__project_id=project_id).count(),
        'total_extractions': Extraction.objects.filter(project__project_id=project_id).count(),
    }

def extract_features_from_paper(project_id, paper_id, group_name, pdf_path):
    """Placeholder for extraction function - will be implemented later"""
    # TODO: Implement actual extraction logic
    return {"status": "extracted", "data": {}}


def prepare_analysis_data(project, schemas_with_stats):
    """
    Prepare aggregated analysis data for all schemas in a project
    Returns structured data for analysis visualization
    """
    analysis_by_schema = []
    
    for item in schemas_with_stats:
        schema = item['schema']
        extractions = item['extractions']
        
        # Get schema fields
        schema_fields = schema.get_fields()
        
        # Aggregate data for each field
        field_aggregations = []
        for field in schema_fields:
            field_id = field.get('id')
            field_name = field.get('name')
            field_type = field.get('type')
            
            # Collect all values for this field across extractions
            values = []
            confidences = []
            
            for extraction in extractions:
                if extraction.status in ['completed', 'verified']:
                    value = extraction.get_field_value(field_id)
                    confidence = extraction.get_field_confidence(field_id)
                    
                    if value is not None:
                        values.append({
                            'paper_title': extraction.paper.title,
                            'paper_id': extraction.paper.paper_id,
                            'extraction_id': extraction.id,  # Add extraction ID
                            'value': value,
                            'confidence': confidence,
                            'status': extraction.status,
                        })
                        if confidence:
                            confidences.append(confidence)
            
            # Calculate statistics
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # For select/multiselect, count occurrences
            value_distribution = {}
            if field_type in ['select', 'multiselect']:
                for item in values:
                    val = item['value']
                    if isinstance(val, list):
                        for v in val:
                            value_distribution[v] = value_distribution.get(v, 0) + 1
                    else:
                        value_distribution[val] = value_distribution.get(val, 0) + 1
            
            field_aggregations.append({
                'field_id': field_id,
                'field_name': field_name,
                'field_type': field_type,
                'total_values': len(values),
                'avg_confidence': round(avg_confidence, 2),
                'values': values,
                'value_distribution': value_distribution,
            })
        
        analysis_by_schema.append({
            'schema': schema,
            'schema_name': schema.name,
            'schema_id': schema.schema_id,
            'total_extractions': len(extractions),
            'verified_count': sum(1 for e in extractions if e.status == 'verified'),
            'completed_count': sum(1 for e in extractions if e.status == 'completed'),
            'field_aggregations': field_aggregations,
        })
    
    return analysis_by_schema


# ============================================================================
# Home & Dashboard
# ============================================================================

def home(request):
    """Dashboard home page"""
    projects = Project.objects.all().order_by('-created_at')[:6]
    
    context = {
        'projects': projects,
        'total_projects': Project.objects.count(),
        'total_papers': Paper.objects.count(),
        'total_extractions': Extraction.objects.count(),
    }
    return render(request, 'dashboard/home.html', context)


# ============================================================================
# Project Management
# ============================================================================

def project_list(request):
    """List all projects"""
    projects = Project.objects.all().order_by('-created_at')
    
    context = {
        'projects': projects,
    }
    return render(request, 'dashboard/project/list.html', context)


def project_detail(request, project_id):
    """Project detail view"""
    project = get_object_or_404(Project, project_id=project_id)
    papers = Paper.objects.filter(project=project).order_by('-updated_at')
    total_papers = papers.count()
    
    # Get project schemas with extraction statistics
    project_schemas = ProjectSchema.objects.filter(
        project=project
    ).select_related('schema').order_by('display_order', '-added_at')
    
    # Calculate extraction stats for each schema
    schemas_with_stats = []
    for ps in project_schemas:
        schema = ps.schema
        
        # Get extractions for this schema in this project
        schema_extractions = Extraction.objects.filter(
            project=project,
            schema=schema
        )
        
        # Count by status
        total_extracted = schema_extractions.count()
        completed = schema_extractions.filter(status='completed').count()
        verified = schema_extractions.filter(status='verified').count()
        failed = schema_extractions.filter(status='failed').count()
        pending = schema_extractions.filter(status='pending').count()
        processing = schema_extractions.filter(status='processing').count()
        
        # Calculate progress
        if total_papers > 0:
            progress_percentage = int((total_extracted / total_papers) * 100)
        else:
            progress_percentage = 0
        
        # Determine progress bar color
        if progress_percentage == 100:
            progress_color = 'success'
        elif progress_percentage >= 75:
            progress_color = 'info'
        elif progress_percentage >= 50:
            progress_color = 'primary'
        elif progress_percentage >= 25:
            progress_color = 'warning'
        else:
            progress_color = 'danger'
        
        schemas_with_stats.append({
            'project_schema': ps,
            'schema': schema,
            'extractions': schema_extractions.select_related('paper').order_by('-updated_at'),
            'stats': {
                'total_papers': total_papers,
                'total_extracted': total_extracted,
                'remaining': total_papers - total_extracted,
                'completed': completed,
                'verified': verified,
                'failed': failed,
                'pending': pending,
                'processing': processing,
                'progress_percentage': progress_percentage,
                'progress_color': progress_color,
            }
        })
    
    # Get recent extractions across all schemas
    extractions = Extraction.objects.filter(project=project).order_by('-created_at')[:10]
    
    # Get papers available in library (not associated with any project or other projects)
    available_papers = Paper.objects.filter(
        Q(project__isnull=True) | ~Q(project=project)
    ).order_by('-updated_at')[:50]  # Limit to recent 50
    
    # Get schemas available in library (not associated with this project)
    available_schemas = Schema.objects.exclude(
        project_associations__project=project
    ).order_by('-created_at')[:50]  # Limit to recent 50
    
    # Get project stats
    stats = get_project_stats(project_id)
    
    # Prepare analysis data
    analysis_data = prepare_analysis_data(project, schemas_with_stats)
    
    context = {
        'project': project,
        'papers': papers,
        'project_schemas': project_schemas,  # Add this for Run Extraction modal
        'schemas_with_stats': schemas_with_stats,
        'available_schemas': available_schemas,
        'extractions': extractions,
        'available_papers': available_papers,
        'stats': stats,
        'analysis_data': analysis_data,
    }
    return render(request, 'dashboard/project/detail.html', context)


def project_create(request):
    """Create new project"""
    if request.method == 'POST':
        project_id = request.POST.get('project_id', '').strip()
        name = request.POST.get('name', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        # Validation
        if not project_id:
            messages.error(request, 'Project ID is required')
            return render(request, 'dashboard/project/create.html')
        
        if not name:
            messages.error(request, 'Project name is required')
            return render(request, 'dashboard/project/create.html')
        
        if Project.objects.filter(project_id=project_id).exists():
            messages.error(request, f'Project ID "{project_id}" already exists')
            return render(request, 'dashboard/project/create.html')
        
        # Create project (no model specified initially)
        project = Project.objects.create(
            project_id=project_id,
            name=name,
            model=None,  # Will be set later in project settings
            notes=notes,
        )
        
        # Create project directory
        project_dir = os.path.join('data', 'projects', project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        messages.success(request, f'Project "{project.name}" created successfully! You can now add papers and configure settings.')
        return redirect('projects:detail', project_id=project_id)  # Redirect to new project detail page
    
    return render(request, 'dashboard/project/create.html')


def project_update(request, project_id):
    """Update project settings"""
    project = get_object_or_404(Project, project_id=project_id)
    
    if request.method == 'POST':
        project.name = request.POST.get('name', '').strip()
        model = request.POST.get('model', '').strip()
        project.model = model if model else None
        project.notes = request.POST.get('notes', '').strip()
        project.save()
        
        messages.success(request, f'Project "{project.name}" settings updated successfully!')
        return redirect('dashboard:project-detail', project_id=project_id)
    
    context = {'project': project}
    return render(request, 'dashboard/project/update.html', context)


@require_http_methods(["POST"])
def project_delete(request, project_id):
    """Delete project (papers remain in library)"""
    project = get_object_or_404(Project, project_id=project_id)
    project_name = project.name
    
    # Unassociate papers (don't delete them - they remain in library)
    Paper.objects.filter(project=project).update(project=None)
    
    # Delete feature groups and their extractions
    ProjectGroup.objects.filter(project=project).delete()
    Extraction.objects.filter(project=project).delete()
    
    # Delete project
    project.delete()
    
    messages.success(
        request, 
        f'Project "{project_name}" deleted successfully! Papers remain in Paper Library.'
    )
    return redirect('dashboard:project-list')


# ============================================================================
# Paper Management
# ============================================================================

def paper_list(request, project_id):
    """List papers in project"""
    project = get_object_or_404(Project, project_id=project_id)
    papers = Paper.objects.filter(project=project).order_by('-created_at')
    
    context = {
        'project': project,
        'papers': papers,
    }
    return render(request, 'dashboard/paper/list.html', context)


def paper_upload(request, project_id):
    """Upload papers to project"""
    project = get_object_or_404(Project, project_id=project_id)
    
    if request.method == 'POST':
        files = request.FILES.getlist('pdf_files')
        
        if not files:
            messages.error(request, 'Please select at least one PDF file')
            return render(request, 'dashboard/paper/upload.html', {'project': project})
        
        uploaded_count = 0
        for pdf_file in files:
            # Validate file type
            if not pdf_file.name.endswith('.pdf'):
                messages.warning(request, f'Skipped non-PDF file: {pdf_file.name}')
                continue
            
            # Generate paper_id from filename
            paper_id = os.path.splitext(pdf_file.name)[0]
            
            # Check if already exists
            if Paper.objects.filter(project=project, paper_id=paper_id).exists():
                messages.warning(request, f'Paper "{paper_id}" already exists')
                continue
            
            # Save PDF file
            project_dir = os.path.join('data', 'projects', project_id)
            os.makedirs(project_dir, exist_ok=True)
            
            pdf_path = os.path.join(project_dir, pdf_file.name)
            with open(pdf_path, 'wb') as f:
                for chunk in pdf_file.chunks():
                    f.write(chunk)
            
            # Create paper record
            Paper.objects.create(
                project=project,
                paper_id=paper_id,
                pdf_path=pdf_path,
            )
            uploaded_count += 1
        
        if uploaded_count > 0:
            messages.success(request, f'Successfully uploaded {uploaded_count} paper(s)!')
        
        return redirect('dashboard:project-detail', project_id=project_id)
    
    context = {'project': project}
    return render(request, 'dashboard/paper/upload.html', context)


@require_http_methods(["POST"])
def paper_delete(request, project_id, paper_id):
    """Delete paper"""
    project = get_object_or_404(Project, project_id=project_id)
    paper = get_object_or_404(Paper, project=project, paper_id=paper_id)
    
    # Delete extractions
    Extraction.objects.filter(paper=paper).delete()
    
    # Delete PDF file
    if paper.pdf_path and os.path.exists(paper.pdf_path):
        try:
            os.remove(paper.pdf_path)
        except Exception as e:
            print(f"Error deleting PDF: {e}")
    
    # Delete paper record
    paper.delete()
    
    messages.success(request, f'Paper "{paper_id}" deleted successfully!')
    return redirect('dashboard:project-detail', project_id=project_id)


# ============================================================================
# Feature Group Management
# ============================================================================

def group_create(request, project_id):
    """Create feature group"""
    project = get_object_or_404(Project, project_id=project_id)
    
    if request.method == 'POST':
        group_name = request.POST.get('group_name', '').strip()
        description = request.POST.get('description', '').strip()
        fields_json = request.POST.get('fields_json', '[]').strip()
        
        if not group_name:
            messages.error(request, 'Group name is required')
            return render(request, 'dashboard/group/create.html', {'project': project})
        
        # Validate JSON
        try:
            fields = json.loads(fields_json)
        except json.JSONDecodeError:
            messages.error(request, 'Invalid JSON format for fields')
            return render(request, 'dashboard/group/create.html', {'project': project})
        
        # Create group
        group = ProjectGroup.objects.create(
            project=project,
            group_name=group_name,
            description=description,
            fields_json=fields_json,
        )
        
        messages.success(request, f'Feature group "{group_name}" created successfully!')
        return redirect('dashboard:project-detail', project_id=project_id)
    
    context = {'project': project}
    return render(request, 'dashboard/group/create.html', context)


def group_update(request, project_id, group_id):
    """Update feature group"""
    project = get_object_or_404(Project, project_id=project_id)
    group = get_object_or_404(ProjectGroup, id=group_id, project=project)
    
    if request.method == 'POST':
        group.group_name = request.POST.get('group_name', '').strip()
        group.description = request.POST.get('description', '').strip()
        group.fields_json = request.POST.get('fields_json', '[]').strip()
        
        # Validate JSON
        try:
            json.loads(group.fields_json)
        except json.JSONDecodeError:
            messages.error(request, 'Invalid JSON format for fields')
            return render(request, 'dashboard/group/update.html', {'project': project, 'group': group})
        
        group.save()
        
        messages.success(request, f'Feature group "{group.group_name}" updated successfully!')
        return redirect('dashboard:project-detail', project_id=project_id)
    
    context = {
        'project': project,
        'group': group,
    }
    return render(request, 'dashboard/group/update.html', context)


@require_http_methods(["POST"])
def group_delete(request, project_id, group_id):
    """Delete feature group"""
    project = get_object_or_404(Project, project_id=project_id)
    group = get_object_or_404(ProjectGroup, id=group_id, project=project)
    group_name = group.group_name
    
    # Note: Extractions are not directly linked to groups, so no need to delete them
    # Extractions are linked to projects and papers, not to feature groups
    
    # Delete group
    group.delete()
    
    messages.success(request, f'Feature group "{group_name}" deleted successfully!')
    return redirect('dashboard:project-detail', project_id=project_id)


# ============================================================================
# Extraction
# ============================================================================

def extraction_run(request, project_id):
    """Run batch extraction"""
    project = get_object_or_404(Project, project_id=project_id)
    papers = Paper.objects.filter(project=project)
    groups = ProjectGroup.objects.filter(project=project)
    
    if request.method == 'POST':
        selected_papers = request.POST.getlist('papers')
        selected_groups = request.POST.getlist('groups')
        
        if not selected_papers or not selected_groups:
            messages.error(request, 'Please select at least one paper and one feature group')
            return render(request, 'dashboard/extraction/run.html', {
                'project': project,
                'papers': papers,
                'groups': groups,
            })
        
        # Run extraction
        success_count = 0
        error_count = 0
        
        for paper_id in selected_papers:
            paper = Paper.objects.get(project=project, paper_id=paper_id)
            
            for group_id in selected_groups:
                group = ProjectGroup.objects.get(id=group_id)
                
                try:
                    # Call extraction function
                    result = extract_features_from_paper(
                        project_id=project_id,
                        paper_id=paper_id,
                        group_name=group.group_name,
                        pdf_path=paper.pdf_path,
                    )
                    
                    # Save extraction
                    Extraction.objects.create(
                        project=project,
                        paper=paper,
                        group=group,
                        result_json=json.dumps(result),
                        status='completed',
                    )
                    success_count += 1
                    
                except Exception as e:
                    Extraction.objects.create(
                        project=project,
                        paper=paper,
                        group=group,
                        result_json=json.dumps({'error': str(e)}),
                        status='failed',
                    )
                    error_count += 1
        
        if success_count > 0:
            messages.success(request, f'Successfully extracted {success_count} result(s)!')
        if error_count > 0:
            messages.warning(request, f'{error_count} extraction(s) failed')
        
        return redirect('dashboard:project-detail', project_id=project_id)
    
    context = {
        'project': project,
        'papers': papers,
        'groups': groups,
    }
    return render(request, 'dashboard/extraction/run.html', context)


def extraction_detail(request, extraction_id):
    """View extraction details"""
    extraction = get_object_or_404(Extraction, id=extraction_id)
    
    # Parse result JSON
    try:
        result = json.loads(extraction.result_json)
    except json.JSONDecodeError:
        result = {}
    
    context = {
        'extraction': extraction,
        'result': result,
    }
    return render(request, 'dashboard/extraction/detail.html', context)


@require_http_methods(["POST"])
def extraction_delete(request, extraction_id):
    """Delete extraction"""
    extraction = get_object_or_404(Extraction, id=extraction_id)
    project_id = extraction.project.project_id
    
    extraction.delete()
    
    messages.success(request, 'Extraction deleted successfully!')
    return redirect('dashboard:project-detail', project_id=project_id)


# ============================================================================
# Analytics
# ============================================================================

def project_analytics(request, project_id):
    """Project analytics dashboard"""
    project = get_object_or_404(Project, project_id=project_id)
    
    # Get all extractions for this project
    extractions = Extraction.objects.filter(project=project)
    
    # Group by status
    status_counts = extractions.values('status').annotate(count=Count('id'))
    
    # Group by feature group
    group_counts = extractions.values('group__group_name').annotate(count=Count('id'))
    
    # Recent extractions
    recent = extractions.order_by('-created_at')[:20]
    
    context = {
        'project': project,
        'total_extractions': extractions.count(),
        'status_counts': status_counts,
        'group_counts': group_counts,
        'recent_extractions': recent,
    }
    return render(request, 'dashboard/analytics/project.html', context)


def global_analytics(request):
    """Global analytics dashboard"""
    # Overall stats
    total_projects = Project.objects.count()
    total_papers = Paper.objects.count()
    total_extractions = Extraction.objects.count()
    total_groups = ProjectGroup.objects.count()
    
    # Recent activity
    recent_projects = Project.objects.order_by('-created_at')[:5]
    recent_extractions = Extraction.objects.order_by('-created_at')[:10]
    
    # Extraction status distribution
    status_counts = Extraction.objects.values('status').annotate(count=Count('id'))
    
    context = {
        'total_projects': total_projects,
        'total_papers': total_papers,
        'total_extractions': total_extractions,
        'total_groups': total_groups,
        'recent_projects': recent_projects,
        'recent_extractions': recent_extractions,
        'status_counts': status_counts,
    }
    return render(request, 'dashboard/analytics/global.html', context)


def project_analysis_export(request, project_id, schema_id=None):
    """
    Export extraction analysis data to CSV, Excel, or JSON
    """
    project = get_object_or_404(Project, project_id=project_id)
    export_format = request.GET.get('format', 'csv')  # csv, json, or excel
    
    # Build query
    queryset = Extraction.objects.filter(project=project, status__in=['completed', 'verified'])
    
    if schema_id:
        schema = get_object_or_404(Schema, schema_id=schema_id)
        queryset = queryset.filter(schema=schema)
        filename_prefix = f"{project_id}_{schema_id}"
    else:
        schema = None
        filename_prefix = f"{project_id}_all_schemas"
    
    extractions = queryset.select_related('paper', 'schema').order_by('schema', 'paper')
    
    if export_format == 'json':
        return export_as_json(extractions, filename_prefix)
    elif export_format == 'csv':
        return export_as_csv(extractions, schema, filename_prefix)
    else:
        messages.error(request, f'Unsupported export format: {export_format}')
        return redirect('dashboard:project-detail', project_id=project_id)


def export_as_json(extractions, filename_prefix):
    """Export extractions as JSON"""
    data = []
    for extraction in extractions:
        item = {
            'extraction_id': extraction.id,
            'paper_id': extraction.paper.paper_id,
            'paper_title': extraction.paper.title,
            'schema_id': extraction.schema.schema_id if extraction.schema else None,
            'schema_name': extraction.schema.name if extraction.schema else None,
            'status': extraction.status,
            'extraction_method': extraction.extraction_method,
            'extracted_data': extraction.get_extracted_data(),
            'created_at': extraction.created_at,
            'updated_at': extraction.updated_at.isoformat() if extraction.updated_at else None,
        }
        data.append(item)
    
    response = HttpResponse(
        json.dumps(data, ensure_ascii=False, indent=2),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_analysis.json"'
    return response


def export_as_csv(extractions, schema, filename_prefix):
    """Export extractions as CSV (flattened structure)"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_analysis.csv"'
    
    # Add BOM for Excel compatibility with UTF-8
    response.write('\ufeff')
    
    writer = csv.writer(response)
    
    # Determine headers
    if schema:
        # Single schema: create columns for each field
        fields = schema.get_fields()
        headers = ['Paper ID', 'Paper Title', 'Status', 'Method']
        field_headers = []
        for field in fields:
            field_headers.append(field['name'])
            field_headers.append(f"{field['name']} (Confidence)")
        headers.extend(field_headers)
        headers.extend(['Created At', 'Updated At'])
        writer.writerow(headers)
        
        # Write data rows
        for extraction in extractions:
            row = [
                extraction.paper.paper_id,
                extraction.paper.title,
                extraction.status,
                extraction.get_extraction_method_display(),
            ]
            
            for field in fields:
                field_id = field['id']
                value = extraction.get_field_value(field_id)
                confidence = extraction.get_field_confidence(field_id)
                
                # Format value
                if isinstance(value, list):
                    value = ', '.join(str(v) for v in value)
                elif value is None:
                    value = ''
                
                row.append(value)
                row.append(confidence if confidence else '')
            
            row.extend([
                extraction.created_at,
                extraction.updated_at.strftime('%Y-%m-%d %H:%M:%S') if extraction.updated_at else '',
            ])
            writer.writerow(row)
    else:
        # Multiple schemas: use generic structure
        headers = ['Schema ID', 'Schema Name', 'Paper ID', 'Paper Title', 
                   'Status', 'Method', 'Extracted Data', 'Created At', 'Updated At']
        writer.writerow(headers)
        
        for extraction in extractions:
            row = [
                extraction.schema.schema_id if extraction.schema else '',
                extraction.schema.name if extraction.schema else '',
                extraction.paper.paper_id,
                extraction.paper.title,
                extraction.status,
                extraction.get_extraction_method_display(),
                json.dumps(extraction.get_extracted_data(), ensure_ascii=False),
                extraction.created_at,
                extraction.updated_at.strftime('%Y-%m-%d %H:%M:%S') if extraction.updated_at else '',
            ]
            writer.writerow(row)
    
    return response
