'''
Django Forms for SMS Extractor Dashboard
'''

from django import forms
from projects.models import Project, ProjectGroup
from papers.models import Paper
import json


class ProjectForm(forms.ModelForm):
    '''Form for creating/editing projects'''
    
    class Meta:
        model = Project
        fields = ['project_id', 'name', 'model', 'notes']
        widgets = {
            'project_id': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ProjectGroupForm(forms.ModelForm):
    '''Form for creating/editing feature groups'''
    
    class Meta:
        model = ProjectGroup
        fields = ['group_name', 'description', 'fields_json']
        widgets = {
            'group_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'fields_json': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PaperUploadForm(forms.Form):
    '''Form for uploading papers'''
    
    pdf_files = forms.FileField(
        required=True,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf',
            'multiple': True
        })
    )
