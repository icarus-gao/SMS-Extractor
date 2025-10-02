from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, FileResponse, Http404
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.core.paginator import Paginator
import re

from .models import Paper
from .forms import PaperUploadForm, PaperSearchForm, BibTeXImportForm


class PaperLibraryView(ListView):
    """Main paper library view - similar to Zotero"""
    model = Paper
    template_name = 'papers/library.html'
    context_object_name = 'papers'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Paper.objects.select_related('project').all()
        
        # Search functionality
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(citation_key__icontains=query) |
                Q(paper_id__icontains=query) |
                Q(title__icontains=query) |
                Q(authors__icontains=query) |
                Q(doi__icontains=query)
            )
        
        # Year filter
        year = self.request.GET.get('year')
        if year:
            queryset = queryset.filter(year=year)
        
        # Project filter
        project_id = self.request.GET.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        # Sorting
        sort_by = self.request.GET.get('sort', '-updated_at')
        if sort_by in ['citation_key', '-citation_key', 'title', '-title', 
                       'year', '-year', 'updated_at', '-updated_at']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = PaperSearchForm(self.request.GET)
        context['total_papers'] = Paper.objects.count()
        context['query'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', '-updated_at')
        
        # Statistics
        from projects.models import Project
        context['total_projects'] = Project.objects.count()
        context['papers_with_pdf'] = Paper.objects.exclude(pdf_file='').exclude(pdf_file__isnull=True).count()
        
        return context


class PaperUploadView(CreateView):
    """Upload new paper with BibTeX support"""
    model = Paper
    form_class = PaperUploadForm
    template_name = 'papers/upload.html'
    success_url = reverse_lazy('papers:library')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, f'Paper "{form.instance.citation_key}" uploaded successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class PaperDetailView(DetailView):
    """View paper details"""
    model = Paper
    template_name = 'papers/detail.html'
    context_object_name = 'paper'
    pk_url_kwarg = 'paper_id'
    
    def get_object(self):
        return get_object_or_404(Paper, paper_id=self.kwargs['paper_id'])


class PaperUpdateView(UpdateView):
    """Edit paper details"""
    model = Paper
    form_class = PaperUploadForm
    template_name = 'papers/edit.html'
    pk_url_kwarg = 'paper_id'
    
    def get_object(self):
        return get_object_or_404(Paper, paper_id=self.kwargs['paper_id'])
    
    def get_success_url(self):
        return reverse_lazy('papers:detail', kwargs={'paper_id': self.object.paper_id})
    
    def form_valid(self, form):
        messages.success(self.request, 'Paper updated successfully!')
        return super().form_valid(form)


class PaperDeleteView(DeleteView):
    """Delete paper"""
    model = Paper
    template_name = 'papers/delete_confirm.html'
    success_url = reverse_lazy('papers:library')
    pk_url_kwarg = 'paper_id'
    
    def get_object(self):
        return get_object_or_404(Paper, paper_id=self.kwargs['paper_id'])
    
    def delete(self, request, *args, **kwargs):
        paper = self.get_object()
        messages.success(request, f'Paper "{paper.citation_key}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


class PaperPDFView(View):
    """Serve PDF file"""
    def get(self, request, paper_id):
        paper = get_object_or_404(Paper, paper_id=paper_id)
        
        if not paper.pdf_file:
            raise Http404("PDF not found")
        
        try:
            return FileResponse(paper.pdf_file.open('rb'), content_type='application/pdf')
        except FileNotFoundError:
            raise Http404("PDF file not found")


class BibTeXImportView(View):
    """Import multiple papers from BibTeX file"""
    def get(self, request):
        form = BibTeXImportForm()
        return render(request, 'papers/import_bibtex.html', {'form': form})
    
    def post(self, request):
        form = BibTeXImportForm(request.POST, request.FILES)
        
        if form.is_valid():
            bibtex_file = request.FILES['bibtex_file']
            project = form.cleaned_data.get('project')
            
            # Read BibTeX file
            try:
                content = bibtex_file.read().decode('utf-8')
            except UnicodeDecodeError:
                messages.error(request, 'Invalid file encoding. Please use UTF-8.')
                return render(request, 'papers/import_bibtex.html', {'form': form})
            
            # Split into individual entries
            entries = re.split(r'(?=@\w+\{)', content)
            imported_count = 0
            error_count = 0
            
            for entry in entries:
                entry = entry.strip()
                if not entry or not entry.startswith('@'):
                    continue
                
                try:
                    # Extract citation key
                    match = re.search(r'@\w+\{([^,\s]+)', entry)
                    if not match:
                        error_count += 1
                        continue
                    
                    citation_key = match.group(1)
                    
                    # Create or update paper
                    paper, created = Paper.objects.update_or_create(
                        paper_id=citation_key,
                        defaults={
                            'citation_key': citation_key,
                            'bibtex_content': entry,
                            'cite_format': 'bibtex',
                            'project': project
                        }
                    )
                    imported_count += 1
                    
                except Exception as e:
                    error_count += 1
                    continue
            
            if imported_count > 0:
                messages.success(request, f'Successfully imported {imported_count} papers.')
            if error_count > 0:
                messages.warning(request, f'{error_count} entries failed to import.')
            
            return redirect('papers:library')
        
        return render(request, 'papers/import_bibtex.html', {'form': form})


# Legacy API views
class PaperListAPIView(View):
    def get(self, request):
        qs = Paper.objects.all().values(
            "paper_id",
            "project_id",
            "title",
            "citation_format",
            "citation_key",
            "year",
            "authors",
            "updated_at",
        )
        return JsonResponse({"papers": list(qs)})


class PaperDetailAPIView(View):
    def get(self, request, paper_id: str):
        try:
            paper = Paper.objects.get(paper_id=paper_id)
        except Paper.DoesNotExist:
            return JsonResponse({"error": "Paper not found"}, status=404)

        data = {
            "paper_id": paper.paper_id,
            "project_id": paper.project_id if paper.project else None,
            "title": paper.title,
            "citation": paper.citation,
            "citation_format": paper.citation_format,
            "citation_key": paper.citation_key,
            "bibtex_content": paper.bibtex_content,
            "authors": paper.authors,
            "year": paper.year,
            "journal": paper.journal,
            "doi": paper.doi,
            "pdf_path": paper.pdf_path,
            "has_pdf": bool(paper.pdf_file),
            "created_at": paper.created_at,
            "updated_at": paper.updated_at,
        }
        return JsonResponse(data)
