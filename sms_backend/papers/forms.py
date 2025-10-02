from django import forms
from django.core.exceptions import ValidationError
import re

from .models import Paper


class PaperUploadForm(forms.ModelForm):
    """Form for uploading papers with BibTeX support"""
    
    paper_id = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., smith2023machine'
        }),
        help_text='Unique identifier for this paper (automatically syncs with citation key)'
    )
    
    cite_format = forms.ChoiceField(
        choices=Paper.CITE_FORMAT_CHOICES,
        initial='bibtex',
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Citation format'
    )
    
    bibtex_content = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control font-monospace',
            'rows': 12,
            'placeholder': '''@article{smith2023machine,
  title={Machine Learning Applications in Healthcare},
  author={Smith, John and Doe, Jane},
  journal={Journal of AI Research},
  year={2023},
  volume={10},
  pages={123--145},
  doi={10.1234/jair.2023.001}
}'''
        }),
        help_text='Paste your BibTeX entry here. Metadata will be auto-extracted.'
    )
    
    pdf_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf'
        }),
        help_text='Upload PDF file (optional)'
    )
    
    # Optional manual fields (if not using BibTeX)
    title = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Paper title'
        })
    )
    
    authors = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Author 1, Author 2, Author 3'
        })
    )
    
    year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '2023'
        })
    )
    
    journal = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Journal name'
        })
    )
    
    doi = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '10.1234/journal.2023.001'
        })
    )
    
    project = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Optionally assign to a project'
    )
    
    class Meta:
        model = Paper
        fields = ['paper_id', 'cite_format', 'bibtex_content', 'pdf_file', 
                  'title', 'authors', 'year', 'journal', 'doi', 'project']
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Load projects for dropdown
        from projects.models import Project
        if user:
            self.fields['project'].queryset = Project.objects.all().order_by('-updated_at')
        else:
            self.fields['project'].queryset = Project.objects.all().order_by('-updated_at')
    
    def clean_paper_id(self):
        """Validate paper_id format"""
        paper_id = self.cleaned_data.get('paper_id')
        
        # Check if it's a valid identifier (alphanumeric, underscore, hyphen)
        if not re.match(r'^[a-zA-Z0-9_-]+$', paper_id):
            raise ValidationError('Paper ID can only contain letters, numbers, underscores, and hyphens.')
        
        return paper_id
    
    def clean_bibtex_content(self):
        """Validate BibTeX format"""
        bibtex = self.cleaned_data.get('bibtex_content')
        
        if bibtex:
            # Check if it looks like valid BibTeX
            if not re.search(r'@\w+\{', bibtex):
                raise ValidationError('Invalid BibTeX format. Must start with @article{, @book{, etc.')
        
        return bibtex
    
    def clean(self):
        cleaned_data = super().clean()
        cite_format = cleaned_data.get('cite_format')
        bibtex_content = cleaned_data.get('bibtex_content')
        title = cleaned_data.get('title')
        
        # If BibTeX format is selected, require BibTeX content or title
        if cite_format == 'bibtex' and not bibtex_content and not title:
            raise ValidationError('Please provide either BibTeX content or enter title manually.')
        
        return cleaned_data
    
    def save(self, commit=True):
        paper = super().save(commit=False)
        
        # Set citation_key to paper_id if not already set
        if not paper.citation_key:
            paper.citation_key = paper.paper_id
        
        # If BibTeX provided, update the citation key in the content
        if paper.bibtex_content and paper.citation_key:
            # Replace any existing citation key with the new one
            paper.bibtex_content = re.sub(
                r'(@\w+\{)[^,\s]+',
                r'\1' + paper.citation_key,
                paper.bibtex_content
            )
        
        if commit:
            paper.save()
        
        return paper


class PaperSearchForm(forms.Form):
    """Form for searching papers"""
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by citation key, title, author, or DOI...',
            'autofocus': True
        })
    )
    
    year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Year'
        })
    )
    
    project = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Filter by Project'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from projects.models import Project
        self.fields['project'].queryset = Project.objects.all().order_by('name')


class BibTeXImportForm(forms.Form):
    """Form for bulk importing papers from BibTeX file"""
    
    bibtex_file = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.bib,.bibtex'
        }),
        help_text='Upload a .bib file containing multiple BibTeX entries'
    )
    
    project = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Optionally assign all papers to a project'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from projects.models import Project
        self.fields['project'].queryset = Project.objects.all().order_by('name')
