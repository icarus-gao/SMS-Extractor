"""
Django Views for SMS Extractor Dashboard
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q
from datetime import datetime, timedelta
import json
import os

from projects.models import Project, ProjectGroup
from papers.models import Paper
from extractions.models import Extraction

# Utility functions will be implemented later or imported correctly
def get_project_stats(project_id):
    """Get project statistics"""
    return {
        'total_papers': Paper.objects.filter(project__project_id=project_id).count(),
        'total_groups': ProjectGroup.objects.filter(project__project_id=project_id).count(),
        'total_extractions': Extraction.objects.filter(project__project_id=project_id).count(),
    }

def extract_features_from_paper(project_id, paper_id, group_name, pdf_path):
    """Placeholder for extraction function - will be implemented later"""
    # TODO: Implement actual extraction logic
    return {"status": "extracted", "data": {}}


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
    groups = ProjectGroup.objects.filter(project=project).order_by('group_name')
    extractions = Extraction.objects.filter(project=project).order_by('-created_at')[:10]
    
    # Get papers available in library (not associated with any project or other projects)
    available_papers = Paper.objects.filter(
        Q(project__isnull=True) | ~Q(project=project)
    ).order_by('-updated_at')[:50]  # Limit to recent 50
    
    # Get project stats
    stats = get_project_stats(project_id)
    
    context = {
        'project': project,
        'papers': papers,
        'groups': groups,
        'extractions': extractions,
        'available_papers': available_papers,
        'stats': stats,
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
    
    # Delete related extractions
    Extraction.objects.filter(group=group).delete()
    
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
