from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView
from django.db.models import Count

from .models import Project, ProjectGroup
from papers.models import Paper


class ProjectListView(View):
    def get(self, request):
        projects = Project.objects.all().values(
            "project_id",
            "name",
            "model",
            "created_at",
            "updated_at",
        )
        return JsonResponse({"projects": list(projects)})


class ProjectDetailView(View):
    def get(self, request, project_id: str):
        try:
            project = Project.objects.get(project_id=project_id)
        except Project.DoesNotExist:
            return JsonResponse({"error": "Project not found"}, status=404)

        groups = ProjectGroup.objects.filter(project=project).values(
            "group_name", "description", "codebook_path", "prompt_path", "updated_at"
        )
        data = {
            "project_id": project.project_id,
            "name": project.name,
            "model": project.model,
            "notes": project.notes,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "feature_groups": list(groups),
        }
        return JsonResponse(data)


# New HTML views for project management
class ProjectListHTMLView(ListView):
    """List all projects with statistics"""
    model = Project
    template_name = 'projects/list.html'
    context_object_name = 'projects'
    
    def get_queryset(self):
        return Project.objects.annotate(
            paper_count=Count('papers')
        ).order_by('-updated_at')


class ProjectDetailHTMLView(DetailView):
    """Project detail page with associated papers"""
    model = Project
    template_name = 'projects/detail.html'
    context_object_name = 'project'
    pk_url_kwarg = 'project_id'
    
    def get_object(self):
        return get_object_or_404(Project, project_id=self.kwargs['project_id'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        # Get papers associated with this project
        context['papers'] = Paper.objects.filter(project=project).order_by('-updated_at')
        context['paper_count'] = context['papers'].count()
        
        # Get unassociated papers for selection
        context['available_papers'] = Paper.objects.filter(project__isnull=True).order_by('-updated_at')
        context['available_count'] = context['available_papers'].count()
        
        # Get feature groups
        context['feature_groups'] = ProjectGroup.objects.filter(project=project)
        
        return context


class AddPaperToProjectView(View):
    """Add a paper to a project"""
    def post(self, request, project_id):
        project = get_object_or_404(Project, project_id=project_id)
        paper_id = request.POST.get('paper_id')
        
        if not paper_id:
            messages.error(request, 'No paper selected.')
            return redirect('projects:detail', project_id=project_id)
        
        try:
            paper = Paper.objects.get(paper_id=paper_id)
            paper.project = project
            paper.save()
            messages.success(request, f'Paper "{paper.citation_key or paper.paper_id}" added to project successfully!')
        except Paper.DoesNotExist:
            messages.error(request, 'Paper not found.')
        
        return redirect('projects:detail', project_id=project_id)


class RemovePaperFromProjectView(View):
    """Remove a paper from a project"""
    def post(self, request, project_id, paper_id):
        project = get_object_or_404(Project, project_id=project_id)
        paper = get_object_or_404(Paper, paper_id=paper_id)
        
        if paper.project != project:
            messages.error(request, 'This paper is not associated with this project.')
        else:
            paper.project = None
            paper.save()
            messages.success(request, f'Paper "{paper.citation_key or paper.paper_id}" removed from project.')
        
        return redirect('projects:detail', project_id=project_id)
